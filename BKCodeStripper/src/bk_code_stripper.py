import json
import os
import signal
import sys
import threading
from urllib.request import urlopen
import pika
from dotenv import load_dotenv
import logging

load_dotenv('../environment/BKstripper.env')

# Global flag for graceful shutdown
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

def get_codes(data_obj_json):
    data = {}
    codes =[]

    if "data" in data_obj_json:
        data = data_obj_json["data"]
    if "categories" in data:
        categories = data["categories"]

        for category in categories:
            items = category["items"]
            for item in items:
                codes.append(item["externalId"])

    return codes # get_codes()

def get_json_from_url(url):
    response = urlopen(url)
    return json.loads(response.read()) # get_json_from_url

def add_meta_code(code_list):
    formatted_list = ["bgk-" + code for code in code_list]
    return formatted_list

def send_codes(rabbit_host, rabbit_port, rabbit_username, rabbit_password, codes, queue_name):
    credentials = pika.PlainCredentials(rabbit_username, rabbit_password)
    parameters = pika.ConnectionParameters(
        host=rabbit_host,
        port=rabbit_port,
        credentials=credentials
    )

    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)

    for code in codes:
        str_code = str(code)
        channel.basic_publish(exchange='', routing_key=queue_name, body=str_code)

    connection.close() # send_codes

def run_code_stripper(RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_USERNAME, RABBITMQ_PASSWORD, bk_url):
    try:
        code_queue_name = os.getenv('CODE_QUEUE_NAME')

        logging.info("Starting the run process...")
        data_json = get_json_from_url(bk_url)
        codes = get_codes(data_json)
        formatted_codes = add_meta_code(codes)
        send_codes(RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_USERNAME, RABBITMQ_PASSWORD, formatted_codes, code_queue_name)
        logging.info("Run process completed successfully.")

    except Exception as e:
        logging.error(f"Error in run process: {e}")

class ThreadConsumeRabbit(threading.Thread):
    def __init__(self,
                 exchange_name,
                 exchange_type,
                 queue_name,
                 callback,
                 rabbit_host,
                 rabbit_port,
                 rabbit_username,
                 rabbit_password,
                 bk_url):
        super().__init__()
        self.exchange_name = exchange_name
        self.exchange_type = exchange_type
        self.queue_name = queue_name
        self.callback = callback
        self.rabbit_host = rabbit_host
        self.rabbit_port = rabbit_port
        self.rabbit_username = rabbit_username
        self.rabbit_password = rabbit_password
        self.bk_url = bk_url
        self.connection = None
        self.channel = None

    def run(self):
        try:
            credentials = pika.PlainCredentials(self.rabbit_username, self.rabbit_password)
            parameters = pika.ConnectionParameters(
                host=self.rabbit_host,
                port=self.rabbit_port,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )

            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()

            # Declare the exchange
            self.channel.exchange_declare(exchange=self.exchange_name, exchange_type=self.exchange_type, durable=True)

            # Declare a temporary queue with a unique name
            result = self.channel.queue_declare(queue='', exclusive=True)
            temp_queue = result.method.queue

            # Bind the temporary queue to the exchange
            self.channel.queue_bind(exchange=self.exchange_name, queue=temp_queue)

            logging.info(f"Waiting for messages in exchange '{self.exchange_name}'")

            # Start consuming
            self.channel.basic_consume(
                queue=temp_queue,
                on_message_callback=self.on_message,
                auto_ack=True
            )

            # Start consuming in a loop
            while not shutdown_flag.is_set():
                self.connection.process_data_events(time_limit=1)

        except pika.exceptions.AMQPConnectionError as e:
            logging.error(f"Connection error: {e}")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
        finally:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                logging.info("RabbitMQ connection closed.")

    def on_message(self, ch, method, properties, body):
        message = body.decode()
        logging.info(f"Received message: {message}")
        if message.strip().lower() == "run":
            logging.info("Received 'run' command. Triggering run_code_stripper() function.")
            run_code_stripper(self.rabbit_host, self.rabbit_port, self.rabbit_username, self.rabbit_password, self.bk_url)

    def stop(self):
        if self.channel:
            self.channel.stop_consuming()
        if self.connection and not self.connection.is_closed:
            self.connection.close()

def graceful_shutdown(signum, frame):
    logging.info(f"Received signal {signum}. Shutting down gracefully...")
    shutdown_flag.set()

def main():
    # RabbitMQ Configuration for Consumer
    exchange_name = os.getenv('FANOUT_EXCHANGE_NAME', 'fanout_logs')
    exchange_type = 'fanout'

    # RabbitMQ Configuration for Publisher
    code_queue_name = os.getenv('CODE_QUEUE_NAME', 'code_queue')

    # RabbitMQ general configuration
    rabbitmq_host = os.getenv('RABBITMQ_HOST', 'localhost')
    rabbitmq_port = int(os.getenv('RABBITMQ_PORT', 5672))
    rabbitmq_username = os.getenv('RABBITMQ_USERNAME', 'guest')
    rabbitmq_password = os.getenv('RABBITMQ_PASSWORD', 'guest')

    # Burger King product catalog URL
    bk_url = os.getenv('BK_URL')

    # Signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)

    # Initialize and start the RabbitMQ consumer thread
    consumer = ThreadConsumeRabbit(
        exchange_name=exchange_name,
        exchange_type=exchange_type,
        queue_name=code_queue_name,
        callback=run_code_stripper,
        rabbit_host=rabbitmq_host,
        rabbit_port=rabbitmq_port,
        rabbit_username=rabbitmq_username,
        rabbit_password=rabbitmq_password,
        bk_url=bk_url
    )

    consumer.start()

    # Wait for shutdown flag
    try:
        while not shutdown_flag.is_set():
            shutdown_flag.wait(timeout=1)
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt received.")
    finally:
        consumer.stop()
        consumer.join()
        logging.info("Application has been shut down gracefully.")


if __name__ == '__main__':
    main()