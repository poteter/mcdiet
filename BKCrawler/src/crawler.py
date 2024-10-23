import json
import os
from urllib.request import urlopen

from dotenv import load_dotenv

load_dotenv('../environment/BKCrawler.env')

def get_codes(data_obj_json):
    data = {}
    if "data" in data_obj_json:
        data = data_obj_json["data"]
    if "categories" in data:
        categories = data["categories"]

        for category in categories:
            print(category["categoryLongName"])
            items = category["items"]
            for item in items:
                print(f'externalId: {item["externalId"]}\nproductName {item["productName"]}\n')

    return "cod"

def get_json_from_url(url):
    response = urlopen(url)
    return json.loads(response.read()) # get_json_from_url

def run():
    bk_url = os.getenv('BK_URL')
    data_json = get_json_from_url(bk_url)
    get_codes(data_json)

if __name__ == '__main__':
    run()