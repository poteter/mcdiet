import os
import pika
import re
import requests
from dotenv import load_dotenv

load_dotenv('environment/MCStripper.env')

def get_codes_from_urls(urls):
    codes = []
    pattern = r'(?:item=|-)(\d+)%'

    for url in urls:
        res = re.findall(pattern, url)
        codes.extend(res)
    int_codes = [eval(i) for i in codes]
    return int_codes # get_codes_from_urls

def get_urls(rabbit_host, rabbit_port, rabbit_username, rabbit_password, queue_name):
    credentials = pika.PlainCredentials(rabbit_username, rabbit_password)
    parameters = pika.ConnectionParameters(
        host=rabbit_host,
        port=rabbit_port,
        credentials=credentials
    )

    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)

    urls = []

    while True:
        method_frame, header_frame, body = channel.basic_get(queue=queue_name, auto_ack=True)

        if method_frame:
            urls.append(body.decode('utf-8'))
        else:
            break

    connection.close()
    return urls # get_urls

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

def run():
    code_queue_name = os.getenv("CODE_QUEUE_NAME")
    url_queue_name = os.getenv("URL_QUEUE_NAME")

    # rabbitMQ Configuration
    rabbitmq_host = os.getenv('RABBITMQ_HOST', 'localhost')
    rabbitmq_port = int(os.getenv('RABBITMQ_PORT', 5672))
    rabbitmq_username = os.getenv('RABBITMQ_USERNAME', 'guest')
    rabbitmq_password = os.getenv('RABBITMQ_PASSWORD', 'guest')

    urls = get_urls(rabbitmq_host, rabbitmq_port, rabbitmq_username, rabbitmq_password, url_queue_name)
    codes = get_codes_from_urls(urls)
    send_codes(rabbitmq_host, rabbitmq_port, rabbitmq_username, rabbitmq_password, codes, code_queue_name)

if __name__ == '__main__':
    run()
