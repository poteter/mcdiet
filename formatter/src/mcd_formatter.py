import json
import os
import logging
import sys
import requests
from urllib.request import urlopen
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

def find_menu_item_data(json_data):
    menu_item_data = {
        "item_id": "",
        "item_name": "",
        "energy_Kcal": 0,
        "food_type": ""
    }

    filter_list = ['McCafé', 'McCafe']

    if "item" in json_data:
        item = json_data["item"]
        logging.info(f"( mcd_formatter.find_menu_item_data ) item")
        if "default_category" in item:
            logging.info(f"( mcd_formatter.find_menu_item_data ) default_category")
            if "category" not in item["default_category"]:
                logging.info(f"( mcd_formatter.find_menu_item_data ) category")
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
                    if nutrient.get("value") == "N/A":
                        menu_item_data["energy_Kcal"] = 0
                    else:
                        string_to_float = float(nutrient.get("value"))
                        float_to_int = int(string_to_float)
                        menu_item_data["energy_Kcal"] = float_to_int
                    break
    logging.info(f"( mcd_formatter.find_menu_item_data ) menu_item_data: {json.dumps(menu_item_data, indent=4)}")
    return menu_item_data # find_menu_item_data

def send_data(data, api_url):
    menu_item_data_formatted = find_menu_item_data(data)

    if menu_item_data_formatted:
        logging.info(json.dumps(menu_item_data_formatted, indent=4))
        try:
            response = requests.post(api_url, json=menu_item_data_formatted)

            if response.status_code == 200:
                logging.info("( mcd_formatter.send_data ) Successfully sent data to the API.")
                logging.info(f"( mcd_formatter.send_data ) Response: {response.json()}")
            else:
                logging.info(f"( mcd_formatter.send_data ) Failed to send data. Status code: {response.status_code}")
                logging.info(f"( mcd_formatter.send_data ) Response: {response.text}")

        except requests.exceptions.RequestException as e:
            logging.error(f"( mcd_formatter.send_data ) An error occurred: {e}")
    else:
        logging.info("( mcd_formatter.send_data ) empty json")

    # send_data

def make_urls_from_codes(code, mc_url):
    url = f"{mc_url}{code}"
    logging.info(f"( mcd_formatter.make_urls_from_codes ) url: {url}")
    return url # make_urls_from_codes

def get_json_from_url(url):
    try:
        response = urlopen(url)
        return json.loads(response.read())  # get_json_from_url
    except logging.error as e:
        logging.error(f"( mcd_formatter.get_json_from_url ) error: {e}")

def send_to_db(url, api_url):
    url_json_object = get_json_from_url(url)
    send_data(url_json_object, api_url)


def run(code):
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

    logging.info(f"(mcd_formatter.run ) codes: {type(code)} {code}")

    db_port = os.getenv('DB_PORT')
    api_url = f'http://{gateway_host_name}:{db_port}/{db_host_name}/api/item'

    mcd_url = os.getenv('MCD_URL')

    url = make_urls_from_codes(code, mcd_url)
    send_to_db(url, api_url)

    # run