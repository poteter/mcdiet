import json
import os

from urllib.request import urlopen

import requests
from dotenv import load_dotenv

def find_menu_item_data(data_obj_json, codes,  api_url):
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
                if item["externalId"] in codes:
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
                    send_data(menu_item_data, api_url)

def send_data(data, api_url):
    if data:
        print(json.dumps(data, indent=4))
        try:
            response = requests.post(api_url, json=data)

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

def get_json_from_url(url):
    response = urlopen(url)
    return json.loads(response.read()) # get_json_from_url

def run(codes):
    path_flag_docker = True
    if path_flag_docker:
        load_dotenv('/app/environment/formatter.env')
    else:
        load_dotenv('../environment/formatter.env')

    db_port = os.getenv('DB_PORT')
    api_url = f'http://localhost:{db_port}/api/item'
    bk_url = os.getenv('BK_URL')
    bk_items = get_json_from_url(bk_url)

    find_menu_item_data(bk_items, codes, api_url)