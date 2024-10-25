import json
import os
from urllib.request import urlopen
import pika
from dotenv import load_dotenv

load_dotenv('../environment/BKstripper.env')

def get_codes(data_obj_json):
    data = {}
    codes =[]

    if "data" in data_obj_json:
        data = data_obj_json["data"]
    if "categories" in data:
        categories = data["categories"]

        for category in categories:
            print(category["categoryLongName"])
            items = category["items"]
            for item in items:
                codes.append(item["externalId"])

    return codes # get_codes()

def get_json_from_url(url):
    response = urlopen(url)
    return json.loads(response.read()) # get_json_from_url

def send_codes(rabbit_host, rabbit_port, rabbit_username, rabbit_password, codes, queue_name):
    credentials = pika.PlainCredentials(rabbit_username, rabbit_password)
    parameters = pika.ConnectionParameters(
        host=rabbit_host,
        port=rabbit_port,
        credentials=credentials
    )

    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    for code in codes:
        str_code = str(code)
        channel.basic_publish(exchange='', routing_key=queue_name, body=str_code)

    connection.close() # send_codes

def run():
    code_queue_name = os.getenv('CODE_QUEUE_NAME')
    bk_url = os.getenv('BK_URL')

    # rabbitMQ Configuration
    RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
    RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
    RABBITMQ_USERNAME = os.getenv('RABBITMQ_USERNAME', 'guest')
    RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'guest')

    data_json = get_json_from_url(bk_url)
    send_codes(RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_USERNAME, RABBITMQ_PASSWORD, get_codes(data_json), code_queue_name)

if __name__ == '__main__':
    run()