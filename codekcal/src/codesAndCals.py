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
        logging.info(f"Converted {type(lst)} items to dict")
        logging.info(f"res_dict {type(res_dict)}")

        return res_dict
    except Exception as e:
        logging.error(f"( convert_list_to_dict ) Error when trying to convert list to dict : {e}")

## get codes and kcal from db
def get_codes_foodtype_and_calories_from_db(uri):
    try:
        response = requests.get(uri)
        logging.info(f"( get_codes_foodtype_and_calories_from_db ) response code: {response.status_code}")
        response.raise_for_status()

        code_cal_foodtype_response = response.json()
        if isinstance(code_cal_foodtype_response, list):
            return code_cal_foodtype_response
        else:
            logging.info(f"( get_codes_foodtype_and_calories_from_db ) Unexpected data format: Expected a list of codes.")
            return []
    except requests.exceptions.RequestException as e:
        logging.error(f"( get_codes_foodtype_and_calories_from_db ) An error occurred: {e}")
        return []

## send pairs to queue
def send_packet_to_queue(channel, codeKcal_queue_name, packet):
    try:
        message = json.dumps(packet)
        logging.info(f"( send_packet_to_queue ) message: {message} ) ")
        channel.basic_publish(
            exchange='',
            routing_key=codeKcal_queue_name,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,
            )
        )
        logging.info(f"( send_packet_to_queue ) Sent message to {codeKcal_queue_name}")
    except Exception as e:
        logging.error(f"( send_packet_to_queue ) Error sending packet: {e}")

def graceful_shutdown(signal, frame):
    shutdown_flag.set()
    logging.info(f"( graceful_shutdown ) Signal {signal} received. Shutting down.")

## makes data packet from param queue parameters and data from the database
def process_message(body, codekcal_queue_name, gw_port, item_db_uri):
    try:
        params = json.loads(body.decode('utf-8'))
        logging.info(f"( process_message ) Processing parameters:{type(params)} {params}")
        param_values = params.values()
        for value in param_values:
            logging.info(f"( process_message ) Processing value {type(value)} {value}")

        # Fetch data from the database
        codes_foodtype_and_calories = get_codes_foodtype_and_calories_from_db(item_db_uri)
        if not codes_foodtype_and_calories:
            logging.info("( process_message ) No data fetched from DB. Skipping packet creation.")
            return

        # Convert list to dictionary
        code_cal_foodtype_dict = convert_list_to_dict(codes_foodtype_and_calories)
        logging.info(f"( process_message ) Processing codes calories: {type(code_cal_foodtype_dict)}")

        # Combine data into a single packet
        packet = {**code_cal_foodtype_dict, **params}


        # Note: The channel will be passed separately
        return packet

    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error: {e}")
    except Exception as e:
        logging.error(f"Error processing message: {e}")

## makes and sends packet to codekcal queue
def on_message(channel, method, properties, body, param_queue_name, codekcal_queue_name, gw_port, item_db_uri):
    logging.info(f"( on_message ) Received message from queue '{param_queue_name}'")

    packet = process_message(body, codekcal_queue_name, gw_port, item_db_uri)

    packet_user = packet.get("user")
    packet_calories = packet.get("calories")
    packet_range = packet.get("range")
    packet_days = packet.get("days")
    packet_mealsPerDay = packet.get("mealsPerDay")

    logging.info(
        f"( process_message ) packet_user: {packet_user} packet_calories: {packet_calories} packet_range: {packet_range} packet_days: {packet_days} packet_mealsPerDay: {packet_mealsPerDay}")
    logging.info(
        f"( process_message ) packet_user: {type(packet_user)} packet_calories: {type(packet_calories)} packet_range: {type(packet_range)} packet_days: {type(packet_days)} packet_mealsPerDay: {type(packet_mealsPerDay)}")

    if packet:
        send_packet_to_queue(channel, codekcal_queue_name, packet)

def create_on_message_callback(param_queue_name, codekcal_queue_name, gw_port, item_db_uri):
    logging.info(f"( create_on_message_callback )")
    def on_message_callback(ch, method, properties, body):
        logging.info(f"( on_message_callback )")
        on_message(ch, method, properties, body, param_queue_name, codekcal_queue_name, gw_port, item_db_uri)
    return on_message_callback


## starts the rabbit channel as a separate thread and consumes the parameter queue
def run_consumer(param_queue_name, codekcal_queue_name, gw_port, item_db_uri, rabbitmq_user, rabbitmq_password, rabbitmq_host):
    if not param_queue_name or not codekcal_queue_name or not gw_port or not item_db_uri:
        logging.error("One or more required environment variables are missing. Exiting.")
        sys.exit(1)

    try:
        # Establish connection
        credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_password)
        connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitmq_host, credentials=credentials))
        channel = connection.channel()

        # Declare the parameter queue
        channel.queue_declare(queue=param_queue_name, durable=True)

        # Define the callback with additional arguments
        channel.basic_consume(
            queue=param_queue_name,
            on_message_callback=create_on_message_callback(param_queue_name, codekcal_queue_name, gw_port, item_db_uri),
            auto_ack=True
        )

        logging.info(f"( run_consumer ) waiting for message from {param_queue_name}")

        # Start consuming in a separate thread to allow graceful shutdown
        consume_thread = threading.Thread(target=channel.start_consuming)
        consume_thread.start()

        while not shutdown_flag.is_set():
            time.sleep(1)

        channel.stop_consuming()
        consume_thread.join()
        connection.close()
        logging.info(f"( run_consumer ) RabbitMQ consumer has been shut down gracefully.")
    except pika.exceptions.AMQPConnectionError as e:
        logging.error(f"( run_consumer ) AMQP connection error: {e}")
    except Exception as e:
        logging.error(f"( run_consumer ) Unexpected error: {e}")

def run():
    path_flag_docker = True
    if path_flag_docker:
        load_dotenv('/app/environment/codeAndCal.env')
    else:
        load_dotenv('../environment/codeAndCal.env')

    param_queue_name = os.getenv("PARAM_QUEUE_NAME")
    codekcal_queue_name = os.getenv("CODEKCAL_QUEUE_NAME")

    if path_flag_docker:
        gateway_host_name = "gateway"
    else:
        gateway_host_name = "localhost"

    item_db_uri = f'http://{gateway_host_name}:{os.getenv("GW_PORT")}/item_db/api/item/codecal'
    logging.info(f"( run ) item_db_uri: {item_db_uri}")
    gw_port = os.getenv("GW_PORT")
    rabbitmq_user = os.getenv('RABBITMQ_USER')
    rabbitmq_password = os.getenv('RABBITMQ_PASS')
    rabbitmq_host = os.getenv('RABBITMQ_HOST')

    # signal handlers
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)

    logging.info("( run ) Starting RabbitMQ consumer.")
    run_consumer(param_queue_name, codekcal_queue_name, gw_port, item_db_uri, rabbitmq_user, rabbitmq_password, rabbitmq_host)
    logging.info("( run ) Consumer stopped.")

if __name__ == '__main__':
    run()