import json
import os

import requests
import pika
from urllib.request import urlopen

from dotenv import load_dotenv

load_dotenv('../../environment/formatter.env')

def find_menu_item_data(json_data):
    menu_item_data = {
        "item_id": 0,
        "item_name": "",
        "energy_Kcal": 0,
        "food_type": ""
    }

    filter_list = ['McCafé', 'McCafe']

    if "item" in json_data:
        item = json_data["item"]

        if "default_category" in item:
            if "category" not in item["default_category"]:
                item_name = item.get("item_name").lower()
                if any(filter_word.lower() in item_name for filter_word in filter_list):
                    food_type = "drink"
                else:
                    food_type = "food"

                menu_item_data["food_type"] = food_type
            elif "category" in item["default_category"]:
                category = item["default_category"]["category"]["name"]
                food_type = "drink" if "drikk" in category.lower() else "food"
                menu_item_data["food_type"] = food_type

        if "item_name" in item:
            menu_item_data["item_name"] = item["item_name"]

        if "item_id" in item:
            menu_item_data["item_id"] = item["item_id"]

        if "nutrient_facts" in item:
            nutrients = item["nutrient_facts"].get("nutrient", [])
            for nutrient in nutrients:
                if nutrient.get("name") == "Energi (kcal)":
                    menu_item_data["energy_Kcal"] = nutrient.get("value")
                    break

    return menu_item_data # find_menu_item_data

def send_data(data, db_port):

    menu_item_data_formatted = find_menu_item_data(data)
    api_url = f'http://localhost:{db_port}/api/item'

    if menu_item_data_formatted:
        print(json.dumps(menu_item_data_formatted, indent=4))
        try:
            response = requests.post(api_url, json=menu_item_data_formatted)

            if response.status_code == 200:
                print("Successfully sent data to the API.")
                print("Response:", response.json())
            else:
                print(f"Failed to send data. Status code: {response.status_code}")
                print("Response:", response.text)

        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
    else:
        print("empty json")

    # send_data

def get_codes(code_queue_name):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    channel.queue_declare(queue=code_queue_name, durable=True)
    codes = []

    while True:
        method_frame, header_frame, body = channel.basic_get(queue=code_queue_name, auto_ack=True)

        if method_frame:
            codes.append(body.decode('utf-8'))
        else:
            break

    connection.close()
    return codes  # get_codes


def make_urls_from_codes(codes, mc_url):
    urls = []
    url = mc_url
    for code in codes:
        urls.append(f"{url}{code}")

    return urls # make_urls_from_codes

def get_json_from_url(url):
    response = urlopen(url)
    return json.loads(response.read()) # get_json_from_url


def run(codes):
    db_port = os.getenv('DB_PORT')
    code_queue_name = os.getenv('CODE_QUEUE_NAME')
    url = os.getenv('URL')

    codes = get_codes(code_queue_name)
    urls = make_urls_from_codes(codes, url)

    for url in urls:
        send_data(get_json_from_url(url), db_port)
    # run