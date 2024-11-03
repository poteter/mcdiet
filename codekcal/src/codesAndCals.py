import json
import logging
import os
import sys
import threading
import signal
import time

import pika
from pika import exceptions
import requests
from dotenv import load_dotenv

load_dotenv('../environment/codeAndCal.env')

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

## converts db data from list to dict
def convert_list_to_dict(lst):
    try:
        res_dict = {item['itemId']: {'energyKcal': item['energyKcal'], 'foodType': item['foodType']} for item in lst}
        return res_dict
    except Exception as e:
        logging.error(f"Error when trying to convert list to dict : {e}")

## get codes and kcal from db
def get_codes_foodtype_and_calories_from_db(uri):
    try:
        response = requests.get(uri)
        response.raise_for_status()

        code_cal_foodtype_response = response.json()
        if isinstance(code_cal_foodtype_response, list):
            return code_cal_foodtype_response
        else:
            print("Unexpected data format: Expected a list of codes.")
            return []
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return []

## send pairs to queue
def send_packet_to_queue(channel, codeKcal_queue_name, packet):
    try:
        message = json.dumps(packet)
        channel.basic_publish(
            exchange='',
            routing_key=codeKcal_queue_name,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,
            )
        )
        logging.info(f"Sent {message} to {codeKcal_queue_name}")
    except Exception as e:
        logging.error(f"Error sending packet: {e}")

def graceful_shutdown(signal, frame):
    shutdown_flag.set()
    logging.info(f"Signal {signal} received. Shutting down.")

## makes data packet from param queue parameters and data from the database
def process_message(body, codekcal_queue_name, gw_port, item_db_uri):
    try:
        params = json.loads(body.decode('utf-8'))
        logging.info(f"Processing parameters: {params}")

        # Fetch data from the database
        codes_foodtype_and_calories = get_codes_foodtype_and_calories_from_db(item_db_uri)
        if not codes_foodtype_and_calories:
            logging.info("No data fetched from DB. Skipping packet creation.")
            return

        # Convert list to dictionary
        code_cal_foodtype_dict = convert_list_to_dict(codes_foodtype_and_calories)

        # Combine data into a single packet
        packet = {**code_cal_foodtype_dict, **params}

        # Note: The channel will be passed separately
        return packet

    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error: {e}")
    except Exception as e:
        logging.error(f"Error processing message: {e}")

## makes and sends packet to codekcal queue
def on_message(channel, method, properties, body, param, args):
    param_queue_name, codekcal_queue_name, gw_port, item_db_uri = args
    logging.info(f"Received message from queue '{param_queue_name}'")

    packet = process_message(body, codekcal_queue_name, gw_port, item_db_uri)
    if packet:
        send_packet_to_queue(channel, codekcal_queue_name, packet)

## starts the rabbit channel as a separate thread and consumes the parameter queue
def run_consumer(param_queue_name, codekcal_queue_name, gw_port, item_db_uri):
    if not param_queue_name or not codekcal_queue_name or not gw_port or not item_db_uri:
        logging.error("One or more required environment variables are missing. Exiting.")
        sys.exit(1)

    try:
        # Establish connection
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()

        # Declare the parameter queue
        channel.queue_declare(queue=param_queue_name, durable=True)

        # Define the callback with additional arguments
        channel.basic_consume(
            queue=param_queue_name,
            on_message_callback=lambda ch, method, properties, body, args: on_message(
                ch, method, properties, body, args, (param_queue_name, codekcal_queue_name, gw_port, item_db_uri)
            ),
            auto_ack=True
        )

        logging.info(f"waiting for message from {param_queue_name}")

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

def run():
    param_queue_name = os.getenv("PARAM_QUEUE_NAME")
    codekcal_queue_name = os.getenv("CODEKCAL_QUEUE_NAME")
    item_db_uri = f'http://localhost:{os.getenv("GW_PORT")}/itemController/api/item/codecal'
    gw_port = os.getenv("GW_PORT")

    # signal handlers
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)

    logging.info("Starting RabbitMQ consumer.")
    run_consumer(param_queue_name, codekcal_queue_name, gw_port, item_db_uri)
    logging.info("Consumer stopped.")

if __name__ == '__main__':
    run()