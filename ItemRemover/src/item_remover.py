import os
import pika
import requests
from dotenv import load_dotenv

load_dotenv('environment/remover.env')

def 

def delete_items(codes, db_port):
    if not db_port:
        raise ValueError("Environment variable 'DB_PORT' is not set.")

    for code in codes:
        api_url = f'http://localhost:{db_port}/api/item/codes/{code}'
        try:
            response = requests.delete(api_url)
            response.raise_for_status()
            print(f"Successfully deleted code: {code}")
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while deleting code {code}: {e}")

    # delete_items