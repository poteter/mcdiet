import json
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

def get_codes_from_db(api_url):
    try:
        response = requests.get(api_url)
        response.raise_for_status()

        codes = response.json()
        if isinstance(codes, list):
            return codes
        else:
            logging.error("Unexpected data format: Expected a list of codes.")
            return []
    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred: {e}")
        return []
    # get_codes_from_db

## returns a list of item codes that is not in the database but is in queue
def get_new_item_codes(queue_codes, db_codes):
    queue_codes = queue_codes.split(',')  # Adjust the delimiter as needed
    queue_codes = [code.strip() for code in queue_codes if code.strip()]
    return list(set(queue_codes) - set(db_codes)) # get_new_item_codes

## returns a list of item codes that is in the queue but not in database
def get_non_carry_item_codes(queue_codes, db_codes):
    return list(set(db_codes) - set(queue_codes)) # get_non_carry_item_codes

def send_codes(codes, queue_name, channel):
    logging.info(f"( send_codes ) Sending {len(codes)} codes to {queue_name} on channel {channel}")
    for code in codes:
        str_code = str(code)
        logging.info(f"( send_codes ) Sending {str_code}")
        channel.basic_publish(exchange='', routing_key=queue_name, body=str_code)

def create_on_message_callback(carry_code_queue, non_carry_code_queue, api_url):
    logging.info(f"( create_on_message_callback ) create_on_message_callback")
    def on_message_callback(ch, method, properties, body):
        logging.info(f"( on_message_callback ) on_message_callback")
        on_message(ch, method, properties, body, carry_code_queue, non_carry_code_queue, api_url)
    return on_message_callback

def on_message(ch, method, properties, body, carry_code_queue, non_carry_code_queue, api_url):

    # get codes from database and code queue
    db_codes = get_codes_from_db(api_url)
    logging.info(f"( on_message ) db_codes: {db_codes} {type(db_codes)}")

    queue_codes = body.decode('utf-8')
    logging.info(f"( on_message ) queue_codes: {queue_codes} {type(queue_codes)}")

    # get lists of new and deprecated item codes
    new_item_codes = get_new_item_codes(queue_codes, db_codes)
    logging.info(f"( on_message ) new_item_codes: {new_item_codes}")
    non_carry_item_codes = get_non_carry_item_codes(queue_codes, db_codes)
    logging.info(f"( on_message ) non_carry_item_codes: {non_carry_item_codes}")

    # send codes of new items to the new item queue
    send_codes(new_item_codes, carry_code_queue, ch)

    #  send codes of items no longer carried to the non carry item queue
    send_codes(non_carry_item_codes, non_carry_code_queue, ch) # on_message

def run_consumer(carry_code_queue, non_carry_code_queue, code_queue_name, api_url, rabbitmq_username, rabbitmq_password, rabbitmq_host):
    if not carry_code_queue or not non_carry_code_queue or not code_queue_name or not api_url:
        logging.error("One or more required environment variables are missing. Exiting.")
        sys.exit(1)

    try:

        # Establish connection
        credentials = pika.PlainCredentials(rabbitmq_username, rabbitmq_password)
        connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitmq_host, credentials=credentials))
        channel = connection.channel()

        # Declare the parameter queue
        channel.queue_declare(queue=code_queue_name, durable=True)

        # Define the callback with additional arguments
        channel.basic_consume(
            queue=code_queue_name,
            on_message_callback=create_on_message_callback(carry_code_queue, non_carry_code_queue, api_url),
            auto_ack=True
        )

        logging.info(f"waiting for message from {code_queue_name}")

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
        load_dotenv('/app/environment/dupe.env')
    else:
        load_dotenv('../environment/dupe.env')

    db_port = os.getenv('DB_PORT')
    carry_code_queue = os.getenv('CARRY_CODES_QUEUE_NAME')
    non_carry_code_queue = os.getenv('NON_CARRY_CODES_QUEUE_NAME')
    code_queue_name = os.getenv('CODE_QUEUE_NAME')
    rabbitmq_username = os.getenv('RABBITMQ_USERNAME')
    rabbitmq_password = os.getenv('RABBITMQ_PASSWORD')
    rabbitmq_host = os.getenv('RABBITMQ_HOST')

    # database GET request uri for all item codes
    api_url = f'http://localhost:{db_port}/api/item/codes'

    # signal handlers
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)

    logging.info("Starting RabbitMQ consumer.")
    run_consumer(carry_code_queue, non_carry_code_queue, code_queue_name, api_url, rabbitmq_username, rabbitmq_password, rabbitmq_host)
    logging.info("Consumer stopped.")
    # run

if __name__ == '__main__':
    run()