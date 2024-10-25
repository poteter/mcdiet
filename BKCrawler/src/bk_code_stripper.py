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

def send_codes(codes, queue_name):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)

    for code in codes:
        str_code = str(code)
        channel.basic_publish(exchange='', routing_key=queue_name, body=str_code)

    connection.close() # send_codes

def run():
    code_queue_name = os.getenv('CODE_QUEUE_NAME')
    bk_url = os.getenv('BK_URL')

    data_json = get_json_from_url(bk_url)
    send_codes(get_codes(data_json), code_queue_name)

if __name__ == '__main__':
    run()