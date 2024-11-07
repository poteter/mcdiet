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

def get_codes_from_urls(urls):
    codes = []
    pattern = r'(?:item=|-)(\d+)%'

    for url in urls:
        res = re.findall(pattern, url)
        codes.extend(res)
    int_codes = [eval(i) for i in codes]
    return int_codes # get_codes_from_urls

def send_codes(codes, queue_name, ch):
    ch.queue_declare(queue=queue_name, durable=True)

    for code in codes:
        str_code = str(code)
        ch.basic_publish(exchange='', routing_key=queue_name, body=str_code)
    # send_codes

def add_meta_code(code_list):
    formatted_list = ["mcd-" + code for code in code_list]
    return formatted_list

def on_message(ch, method, properties, body, param, args):
    url_queue_name, code_queue_name = args

    urls = body.decode('utf-8')
    codes = get_codes_from_urls(urls)
    formatted_codes = add_meta_code(codes)
    send_codes(formatted_codes, code_queue_name, ch)

def run_consumer(code_queue_name, url_queue_name, rabbitmq_user, rabbitmq_password):
    if not code_queue_name or not url_queue_name:
        logging.error("One or more required environment variables are missing. Exiting.")
        sys.exit(1)

    try:
        # Establish connection
        credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_password)
        connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq', credentials=credentials))
        channel = connection.channel()

        # Declare the parameter queue
        channel.queue_declare(queue=code_queue_name, durable=True)

        # Define the callback with additional arguments
        channel.basic_consume(
            queue=code_queue_name,
            on_message_callback=lambda ch, method, properties, body, param, args: on_message(
                ch, method, properties, body, args, (url_queue_name, code_queue_name)
            ),
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

    logging.info("Starting RabbitMQ consumer.")
    run_consumer(code_queue_name, url_queue_name, rabbitmq_user, rabbitmq_password)
    logging.info("Consumer stopped.")

if __name__ == '__main__':
    run()
