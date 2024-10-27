import os
import pika
import requests
from dotenv import load_dotenv

load_dotenv('environment/remover.env')

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

def delete_items(codes, db_port):
    if not db_port:
        raise ValueError("Environment variable 'DB_PORT' is not set.")

    for code in codes:
        api_url = f'http://localhost:{db_port}/api/item/codes/{code}'
        try:
            response = requests.delete(api_url)
            response.raise_for_status()
            print(f"Successfully deleted code: {code}")
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while deleting code {code}: {e}")

    # delete_items

def run():
    db_port = os.getenv('DB_PORT')
    non_carry_code_queue = os.getenv('NON_CARRY_CODES_QUEUE_NAME')

    # rabbitMQ Configuration
    rabbitmq_host = os.getenv('RABBITMQ_HOST', 'localhost')
    rabbitmq_port = int(os.getenv('RABBITMQ_PORT', 5672))
    rabbitmq_username = os.getenv('RABBITMQ_USERNAME', 'guest')
    rabbitmq_password = os.getenv('RABBITMQ_PASSWORD', 'guest')

    queue_codes = get_codes_from_queue(non_carry_code_queue, rabbitmq_host, rabbitmq_port, rabbitmq_username, rabbitmq_password)
    delete_items(queue_codes, db_port)
    # run

if __name__ == '__main__':
    run()