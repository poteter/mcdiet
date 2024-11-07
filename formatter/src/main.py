import logging
import signal
import sys
import threading
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

# sort list of codes from the queue into sub-lists of codes by their meta code
# and strips meta code from queue code
# mcd-500232 -> 500232
# bgk-4835-fsd4123-324f -> 4835-fsd4123-324f
def sort_codes(code_list, meta_code):
    result_list = []
    for code in code_list:
        if meta_code in code:
            result_list.append(code.replace(meta_code, ''))
    return result_list
    # sort_codes

def graceful_shutdown(signal, frame):
    shutdown_flag.set()
    logging.info(f"Signal {signal} received. Shutting down.")

def on_message(channel, method, properties, body, param):

    # sorts codes by meta code
    queue_codes = body.decode('utf-8')

    # calls the formatter modules
    bk_formatter.run(sort_codes(queue_codes, "bgk-"))
    mcd_formatter.run(sort_codes(queue_codes, "mcd-"))
    # on_message

def run_consumer(carry_code_queue, rabbitmq_username, rabbitmq_password):
    if not carry_code_queue:
        logging.error("One or more required environment variables are missing. Exiting.")
        sys.exit(1)

    try:
        # Establish connection
        credentials = pika.PlainCredentials(rabbitmq_username, rabbitmq_password)
        connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq', credentials=credentials))
        channel = connection.channel()

        # Declare the parameter queue
        channel.queue_declare(queue=carry_code_queue, durable=True)

        # Define the callback with additional arguments
        channel.basic_consume(
            queue=carry_code_queue,
            on_message_callback=lambda ch, method, properties, body, param: on_message(
                ch, method, properties, body, param
            ),
            auto_ack=True
        )

        logging.info(f"waiting for message from {carry_code_queue}")

        # Start consuming in a separate thread to allow graceful shutdown
        consume_thread = threading.Thread(target=channel.start_consuming)
        consume_thread.start()

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

    # signal handlers
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)

    logging.info("Starting RabbitMQ consumer.")
    run_consumer(carry_code_queue, rabbitmq_username, rabbitmq_password)
    logging.info("Consumer stopped.")

if __name__ == '__main__':
    run()