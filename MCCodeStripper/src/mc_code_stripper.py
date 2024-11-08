import logging
import os
import sys
import threading
import time
import pika
import re
from dotenv import load_dotenv
from pika import exceptions

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

def get_codes_from_urls(url):
    codes = []
    pattern = r'(?:item=|-)(\d+)%'

    res = re.findall(pattern, url)
    codes.extend(res)

    return codes # get_codes_from_urls

def send_codes(codes, queue_name, ch):
    ch.queue_declare(queue=queue_name, durable=True)
    logging.info(f"( send_codes ) queue_name: {queue_name}")

    str_codes = str(codes)
    logging.info(f"( send_codes ) str_code: {str_codes}")

    ch.basic_publish(exchange='', routing_key=queue_name, body=str_codes)
    # send_codes

def add_meta_code(code_list):
    formatted_list = ["mcd-" + code for code in code_list]
    return formatted_list

def create_on_message_callback(url_queue_name, code_queue_name):
    logging.info(f"( create_on_message_callback ) create_on_message_callback")
    def on_message_callback(ch, method, properties, body):
        logging.info(f"( on_message_callback ) on_message_callback")
        on_message(ch, method, properties, body, url_queue_name, code_queue_name)
    return on_message_callback

def on_message(ch, method, properties, body, url_queue_name, code_queue_name):
    logging.info(f"( on_message ) on_message")
    urls = body.decode('utf-8')
    logging.info(f"( on_message ) urls: {urls}")

    codes = get_codes_from_urls(urls)
    logging.info(f"( on_message ) codes: {codes}")

    formatted_codes = add_meta_code(codes)
    logging.info(f"( on_message ) formatted_codes: {formatted_codes}")

    send_codes(formatted_codes, code_queue_name, ch)

def run_consumer(code_queue_name, url_queue_name, rabbitmq_user, rabbitmq_password, rabbitmq_host):
    if not code_queue_name or not url_queue_name:
        logging.error("One or more required environment variables are missing. Exiting.")
        sys.exit(1)

    try:
        # Establish connection
        credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_password)
        connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitmq_host, credentials=credentials))
        channel = connection.channel()

        # Declare the parameter queue
        channel.queue_declare(queue=url_queue_name, durable=True)

        # Define the callback with additional arguments
        channel.basic_consume(
            queue=url_queue_name,
            on_message_callback=create_on_message_callback(url_queue_name, code_queue_name),
            auto_ack=True
        )

        logging.info(f"waiting for message from {url_queue_name}")

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

def run():
    path_flag_docker = True
    if path_flag_docker:
        load_dotenv('/app/environment/MCStripper.env')
    else:
        load_dotenv('../environment/MCStripper.env')

    code_queue_name = os.getenv("CODE_QUEUE_NAME")
    url_queue_name = os.getenv("URL_QUEUE_NAME")
    rabbitmq_user = os.getenv("RABBITMQ_USERNAME")
    rabbitmq_password = os.getenv("RABBITMQ_PASSWORD")
    rabbitmq_host = os.getenv("RABBITMQ_HOST")

    logging.info(f"code_queue_name: {code_queue_name}, url_queue_name: {url_queue_name}, rabbitmq_user: {rabbitmq_user}, rabbitmq_password: {rabbitmq_password}")

    logging.info("Starting RabbitMQ consumer.")
    run_consumer(code_queue_name, url_queue_name, rabbitmq_user, rabbitmq_password, rabbitmq_host)
    logging.info("Consumer stopped.")

if __name__ == '__main__':
    run()
