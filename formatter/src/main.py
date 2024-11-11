import logging
import signal
import sys
import threading
import time

from pika import exceptions
import pika
import os
from dotenv import load_dotenv
import bk_formatter, mcd_formatter

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

# strips meta code from queue code
# mcd-500232 -> 500232
# bgk-4835-fsd4123-324f -> 4835-fsd4123-324f
def sort_codes(codes, meta_code):
    logging.info(f"( sort_codes {meta_code})")
    trimmed_codes = []

    for code in codes:
        logging.info(f"( sort_codes {code})")
        if meta_code in code:
            trimmed_code = code.replace(meta_code, '')
            trimmed_code = trimmed_code.replace("]", '')
            trimmed_code = trimmed_code.replace("[", '')
            trimmed_code = trimmed_code.replace("'", '')
            trimmed_code = trimmed_code.replace("/", '')
            trimmed_code = trimmed_code.replace("\\", '')
            logging.info(f"( trimmed_code {trimmed_code})")
            trimmed_codes.append(trimmed_code)

    logging.info(f"( sort_codes ) result_list: {trimmed_codes}")
    return trimmed_codes
    # sort_codes

def graceful_shutdown(signal, frame):
    shutdown_flag.set()
    logging.info(f"Signal {signal} received. Shutting down.")

def on_message(channel, method, properties, body):
    # sorts codes by meta code
    bytes_to_string = body.decode()
    string_to_list = bytes_to_string.split(",")
    logging.info(f"( on_message ) queue_codes: {type(string_to_list)} {string_to_list}")

    # calls the formatter modules
    logging.info(f"( run_consumer ) bk_formatter 'bkg-'")
    bk_codes = sort_codes(string_to_list, "bgk-")
    if bk_codes is not None:
        bk_formatter.run(bk_codes)

    logging.info(f"( run_consumer ) mcd_formatter 'mcd-'")
    mcd_codes = sort_codes(string_to_list, "mcd-")
    if mcd_codes is not None:
        mcd_formatter.run(mcd_codes)
    # on_message

def run_consumer(carry_code_queue, rabbitmq_username, rabbitmq_password, rabbitmq_host):
    if not carry_code_queue:
        logging.error("One or more required environment variables are missing. Exiting.")
        sys.exit(1)

    try:
        logging.info(f"( run_consumer )")
        # Establish connection
        credentials = pika.PlainCredentials(rabbitmq_username, rabbitmq_password)
        connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitmq_host, credentials=credentials))
        channel = connection.channel()

        # Declare the parameter queue
        channel.queue_declare(queue=carry_code_queue, durable=True)

        # Define the callback with additional arguments
        channel.basic_consume(
            queue=carry_code_queue,
            on_message_callback=lambda ch, method, properties, body: on_message(
                ch, method, properties, body
            ),
            auto_ack=True
        )

        logging.info(f"waiting for message from {carry_code_queue}")

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
        load_dotenv('/app/environment/formatter.env')
    else:
        load_dotenv('../environment/formatter.env')

    carry_code_queue = os.getenv('CODE_QUEUE_NAME')
    rabbitmq_username = os.getenv('RABBITMQ_USERNAME')
    rabbitmq_password = os.getenv('RABBITMQ_PASSWORD')
    rabbitmq_host = os.getenv('RABBITMQ_HOST')

    # signal handlers
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)

    logging.info("( run ) Starting RabbitMQ consumer.")
    run_consumer(carry_code_queue, rabbitmq_username, rabbitmq_password, rabbitmq_host)
    logging.info("( run ) Consumer stopped.")

if __name__ == '__main__':
    run()