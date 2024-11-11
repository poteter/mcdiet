import json
import os
import sys

from urllib.request import urlopen

import logging
import requests
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("server.log")
    ]
)

def find_menu_item_data(data_obj_json, code):
    logging.info(f"( bk_formatter.find_menu_item_data )")
    menu_item_data = {
        "item_id": "",
        "item_name": "",
        "energy_Kcal": 0,
        "food_type": ""
    }
    logging.info(f"( bk_formatter.find_menu_item_data ) menu_item_data: {json.dumps(menu_item_data)}")
    filter_list = ['kaffe', 'Espresso', 'Cappuccino', 'Milkshakes', 'drinks']

    data = {}
    if "data" in data_obj_json:
        logging.info(f"( bk_formatter.find_menu_item_data ) data")
        data = data_obj_json["data"]
    if "categories" in data:
        logging.info(f"( bk_formatter.find_menu_item_data ) category")
        categories = data["categories"]

        for category in categories:
            items = category["items"]
            category_name = category.get("categoryLongName").lower()
            for item in items:
                if item["externalId"] in code:
                    logging.info(f"( bk_formatter.find_menu_item_data ) externalId: {item['externalId']}")
                    menu_item_data['item_id'] = item["externalId"]
                    menu_item_data['item_name'] = item["productName"]
                    string_to_float = float(item["calories"])
                    float_to_int = int(string_to_float)
                    menu_item_data['energy_Kcal'] = float_to_int

                    item_name = item.get("productName").lower()

                    if any(filter_word.lower() in item_name for filter_word in filter_list):
                        menu_item_data['food_type'] = "drink"
                    elif any(filter_word.lower() in category_name for filter_word in filter_list):
                        menu_item_data['food_type'] = "drink"
                    else:
                        menu_item_data['food_type'] = "food"
                    logging.info(f"( bk_formatter.find_menu_item_data ) menu_item_data: {menu_item_data}")
                    return menu_item_data

def send_data(items, api_url):
    if items:
        logging.info(f"( bk_formatter.send_data ) items: {type(items)}")
        for item in items:
            try:
                response = requests.post(api_url, json=item)

                if response.status_code == 200:
                    logging.info("( bk_formatter.send_data ) Successfully sent data to the API.")
                    logging.info(f"( bk_formatter.send_data ) Response: {json.dumps(response.json(), indent=4)}")
                else:
                    logging.error(
                        f"( bk_formatter.send_data ) Failed to send data. Status code: {response.status_code}")
                    logging.error(f"( bk_formatter.send_data ) Response: {json.dumps(response.json(), indent=4)}")

            except requests.exceptions.RequestException as e:
                logging.error(f"( bk_formatter.send_data ) An error occurred: {e}")
    else:
        logging.error(f"( bk_formatter.send_data ) empty json")
    # send_data

def get_json_from_url(url):
    response = urlopen(url)
    return json.loads(response.read()) # get_json_from_url

def test():
    response = requests.get("http://gateway:8081/item_db/api/item/test")
    if response.status_code == 200:
        logging.info(f"( bk_formatter.test ) response: {response.text}")
    else:
        logging.error(f"( bk_formatter.test ) response status code: {response.status_code}")

def run_sequence(bk_items, codes, api_url):
    items = []
    for code in codes:
        items.append(find_menu_item_data(bk_items, code))

    send_data(items, api_url)

def run(codes):
    path_flag_docker = True
    if path_flag_docker:
        load_dotenv('/app/environment/formatter.env')
    else:
        load_dotenv('../environment/formatter.env')

    if path_flag_docker:
        db_host_name = 'item_db'
    else:
        db_host_name = 'localhost'

    if path_flag_docker:
        gateway_host_name = 'gateway'
    else:
        gateway_host_name = 'localhost'

    logging.info(f"( bk_formatter.run ) codes: {type(codes)} {codes}")

    db_port = os.getenv('DB_PORT')
    api_url = f'http://{gateway_host_name}:{db_port}/{db_host_name}/api/item'

    #test()

    logging.info(f"( bk_formatter.run ) api_url: {api_url}")
    bk_url = os.getenv('BK_URL')
    logging.info(f"( bk_formatter.run ) bk_url: {bk_url}")
    bk_items = get_json_from_url(bk_url)
    #logging.info(f"( run ) bk_items: {json.dumps(bk_items, indent=4)}")
    run_sequence(bk_items, codes, api_url)
