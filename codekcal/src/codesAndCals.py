import json
import os

import pika
import requests
from dotenv import load_dotenv

load_dotenv('../environment/codeAndCal.env')

## get parameters from queue
def get_parameters_from_queue(queue_name):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    channel.queue_declare(queue=queue_name, durable=True)

    params = ""

    method_frame, header_frame, body = channel.basic_get(queue=queue_name, auto_ack=True)

    if method_frame:
        params = body.decode('utf-8')

    connection.close()
    return json.loads(params)

def convert_list_to_dict(lst):
    res_dict = {item['itemId']: {'energyKcal': item['energyKcal'], 'foodType': item['foodType']} for item in lst}
    return res_dict

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
def send_packet_to_queue(queue_name, packet):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)

    message = json.dumps(packet)
    channel.basic_publish(exchange='', routing_key=queue_name, body=message)
    connection.close()

def run():
    param_queue_name = os.getenv("PARAM_QUEUE_NAME")
    codekcal_queue_name = os.getenv("CODEKCAL_QUEUE_NAME")
    item_db_uri = f'http://localhost:{os.getenv("GW_PORT")}/itemController/api/item/codecal'
    code_cal_foodtype = convert_list_to_dict(get_codes_foodtype_and_calories_from_db(item_db_uri))
    params = get_parameters_from_queue(param_queue_name)

    packet = dict(code_cal_foodtype)
    packet.update(params)

    send_packet_to_queue(codekcal_queue_name, packet)

if __name__ == '__main__':
    run()