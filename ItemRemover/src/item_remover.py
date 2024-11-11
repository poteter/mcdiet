import logging
import os
import signal
import sys
import threading
import time
from pika import exceptions
import pika
import requests
from dotenv import load_dotenv

# global flag
shutdown_flag = threading.Event()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("server.log")
    ]
)

def delete_items(codes, db_port, api_url):
    if not db_port:
        logging.error("db_port is empty")

    for code in codes:
        trimmed_code = code.replace("]", '')
        trimmed_code = trimmed_code.replace("[", '')
        trimmed_code = trimmed_code.replace("'", '')
        trimmed_code = trimmed_code.replace("/", '')
        trimmed_code = trimmed_code.replace("\\", '')
        trimmed_code = trimmed_code.replace('"', '')
        trimmed_code = trimmed_code.replace(" ", '')
        api_url = f'{api_url}{trimmed_code}'
        try:
            response = requests.delete(api_url)
            response.raise_for_status()
            print(f"Successfully deleted code: {trimmed_code}")
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while deleting code {trimmed_code}: {e}")
    # delete_items

def on_message(ch, method, props, body, db_port, api_url):
    queue_code = body.decode('utf-8')
    string_to_list = queue_code.split(',')
    delete_items(string_to_list, db_port, api_url)

def create_on_message_callback(db_port, api_url):
    logging.info(f"( create_on_message_callback ) create_on_message_callback")
    def on_message_callback(ch, method, properties, body):
        logging.info(f"( on_message_callback ) on_message_callback")
        on_message(ch, method, properties, body, db_port, api_url)
    return on_message_callback

def run_consumer(db_port, non_carry_code_queue, rabbitmq_username, rabbitmq_password, rabbitmq_host, api_url):
    if not db_port:
        logging.error("Environment variable 'DB_PORT' is not set.")
        sys.exit(1)

    try:
        # Establish connection
        credentials = pika.PlainCredentials(rabbitmq_username, rabbitmq_password)
        connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitmq_host, credentials=credentials))
        channel = connection.channel()

        # Declare the parameter queue
        channel.queue_declare(queue=non_carry_code_queue, durable=True)

        # Define the callback with additional arguments
        channel.basic_consume(
            queue=non_carry_code_queue,
            on_message_callback=create_on_message_callback(db_port, api_url),
            auto_ack=True
        )

        logging.info(f"waiting for message from {non_carry_code_queue}")

        # Start consuming in a separate thread to allow graceful shutdown
        consume_thread = threading.Thread(target=channel.start_consuming)
        consume_thread.start()

        while not shutdown_flag.is_set():
            time.sleep(1)

        channel.stop_consuming()
        consume_thread.join()
        connection.close()
        logging.info("RabbitMQ consumer has been shut down gracefully.")

    except pika.exceptions.AMQPConnectionError as e:
        logging.error(f"AMQP connection error: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
    # run_consumer

def graceful_shutdown(signal, frame):
    shutdown_flag.set()
    logging.info(f"Signal {signal} received. Shutting down.")

def run():
    path_flag_docker = True
    if path_flag_docker:
        load_dotenv('/app/environment/remover.env')
    else:
        load_dotenv('../environment/remover.env')

    if path_flag_docker:
        db_host_name = 'item_db'
    else:
        db_host_name = 'localhost'

    if path_flag_docker:
        gateway_host_name = 'gateway'
    else:
        gateway_host_name = 'localhost'

    db_port = os.getenv('DB_PORT')
    api_url = f'http://{gateway_host_name}:{db_port}/{db_host_name}/api/item/codes/'

    non_carry_code_queue = os.getenv('NON_CARRY_CODES_QUEUE_NAME')
    rabbitmq_username = os.getenv('RABBITMQ_USERNAME')
    rabbitmq_password = os.getenv('RABBITMQ_PASSWORD')
    rabbitmq_host = os.getenv('RABBITMQ_HOST')

    # signal handlers
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)

    logging.info("Starting RabbitMQ consumer.")
    run_consumer(non_carry_code_queue, db_port, rabbitmq_username, rabbitmq_password, rabbitmq_host, api_url)
    logging.info("Consumer stopped.")
    # run

if __name__ == '__main__':
    run()