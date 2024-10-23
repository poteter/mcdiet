import json
import os

import requests
import pika
from urllib.request import urlopen

from dotenv import load_dotenv

load_dotenv('../environment/formatter.env')

def find_menu_item_data(data_obj_json):
    menu_item_data = {
        "item_id": 0,
        "item_name": "",
        "energy_Kcal": 0,
        "food_type": ""
    }
    filter_list = ['kaffe', 'Espresso', 'Cappuccino', 'Milkshakes', 'drinks']

    data = {}
    if "data" in data_obj_json:
        data = data_obj_json["data"]
    if "categories" in data:
        categories = data["categories"]

        for category in categories:
            items = category["items"]
            category_name = category.get("categoryLongName").lower()
            for item in items:
                menu_item_data['item_id'] = item["externalId"]
                menu_item_data['item_name'] = item["productName"]
                menu_item_data['energy_Kcal'] = item["calories"]

                item_name = item.get("productName").lower()

                if any(filter_word.lower() in item_name for filter_word in filter_list):
                    menu_item_data['food_type'] = "drink"
                elif any(filter_word.lower() in category_name for filter_word in filter_list):
                    menu_item_data['food_type'] = "drink"
                else:
                    menu_item_data['food_type'] = "food"
                send_to_item_db(menu_item_data)

def send_to_item_db(json_item):
    print(json.dumps(json_item, indent=4))


def get_json_from_url(url):
    response = urlopen(url)
    return json.loads(response.read()) # get_json_from_url

def run():
    bk_url = os.getenv('BK_URL')
    data_json = get_json_from_url(bk_url)
    find_menu_item_data(data_json)

if __name__ == '__main__':
    run()