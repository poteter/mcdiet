import os
import pika
import requests
from dotenv import load_dotenv

load_dotenv('../environment/dupe.env')

def get_codes_from_db(db_port):
    api_url = f'http://localhost:{db_port}/api/item/codes'
    try:
        response = requests.get(api_url)
        response.raise_for_status()

        codes = response.json()
        if isinstance(codes, list):
            return codes
        else:
            print("Unexpected data format: Expected a list of codes.")
            return []
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return []
    # get_codes_from_db

def get_new_item_codes(queue_codes, db_codes):
    return list(set(queue_codes) - set(db_codes)) # get_new_item_codes

def get_non_carry_item_codes(queue_codes, db_codes):
    return list(set(db_codes) - set(queue_codes)) # get_non_carry_item_codes

def get_codes_from_queue(queue_name, rabbit_host, rabbit_port, rabbit_username, rabbit_password):
    codes = []
    credentials = pika.PlainCredentials(rabbit_username, rabbit_password)
    parameters = pika.ConnectionParameters(
        host=rabbit_host,
        port=rabbit_port,
        credentials=credentials
    )

    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)

    while True:
        method_frame, header_frame, body = channel.basic_get(queue=queue_name, auto_ack=True)

        if method_frame:
            codes.append(body.decode('utf-8'))
        else:
            break

    connection.close()
    return codes # get_codes_from_queue

def send_codes(codes, queue_name, rabbit_host, rabbit_port, rabbit_username, rabbit_password):
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

    connection.close()  # send_carry_code

def run():
    db_port = os.getenv('DB_PORT')
    carry_code_queue = os.getenv('CARRY_CODES_QUEUE_NAME')
    non_carry_code_queue = os.getenv('NON_CARRY_CODES_QUEUE_NAME')
    code_queue_name = os.getenv('CODE_QUEUE_NAME')

    # rabbitMQ Configuration
    rabbitmq_host = os.getenv('RABBITMQ_HOST', 'localhost')
    rabbitmq_port = int(os.getenv('RABBITMQ_PORT', 5672))
    rabbitmq_username = os.getenv('RABBITMQ_USERNAME', 'guest')
    rabbitmq_password = os.getenv('RABBITMQ_PASSWORD', 'guest')

    # get codes from database and code queue
    db_codes = get_codes_from_db(db_port)
    queue_codes = get_codes_from_queue(code_queue_name, rabbitmq_host, rabbitmq_port, rabbitmq_username, rabbitmq_password)

    # get lists of new and deprecated item codes
    new_item_codes = get_new_item_codes(queue_codes, db_codes)
    non_carry_item_codes = get_non_carry_item_codes(queue_codes, db_codes)

    # send codes of new items to the new item queue
    send_codes(new_item_codes, carry_code_queue, rabbitmq_host, rabbitmq_port, rabbitmq_username, rabbitmq_password)

    #  send codes of items no longer carried to the non carry item queue
    send_codes(non_carry_item_codes, non_carry_code_queue, rabbitmq_host, rabbitmq_port, rabbitmq_username, rabbitmq_password)
    # run

if __name__ == '__main__':
    run()