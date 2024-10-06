import os

import pika
import re
import requests
from dotenv import load_dotenv

load_dotenv('environment/dupe.env')

def get_codes_from_urls(urls):
    codes = []
    pattern = r'(?:item=|-)(\d+)%'

    for url in urls:
        res = re.findall(pattern, url)
        codes.extend(res)
    int_codes = [eval(i) for i in codes]
    return int_codes# get_codes_from_urls

def get_codes_from_db(db_port):
    api_url = f'http://localhost:{db_port}/api/item/codes'
    try:
        response = requests.get(api_url)
        response.raise_for_status()

        codes = response.json()
        if isinstance(codes, list):
            return codes
        else:
            print("Unexpected data format: Expected a list of codes.")
            return []
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return []
    # get_codes_from_db

def compare_code_lists(url_codes, db_codes):
    return list(set(url_codes) - set(db_codes)) # compare_code_lists

def delete_deprecated_codes(db_codes, url_codes, db_port):
    if not db_port:
        raise ValueError("Environment variable 'DB_PORT' is not set.")

    codes_to_delete = set(db_codes) - set(url_codes)
    for code in codes_to_delete:
        #print(f"Deleting code: {code}")
        api_url = f'http://localhost:{db_port}/api/item/codes/{code}'
        try:
            response = requests.delete(api_url)
            response.raise_for_status()
            print(f"Successfully deleted code: {code}")
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while deleting code {code}: {e}")

    # delete_deprecated_codes

def get_urls(queue_name):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    channel.queue_declare(queue=queue_name, durable=True)

    urls = []

    while True:
        method_frame, header_frame, body = channel.basic_get(queue=queue_name, auto_ack=True)

        if method_frame:
            urls.append(body.decode('utf-8'))
        else:
            break

    connection.close()
    return urls # get_urls

def send_codes(codes, queue_name):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)

    for code in codes:
        #print(f"Sending code: {code}")
        str_code = str(code)
        channel.basic_publish(exchange='', routing_key=queue_name, body=str_code)

    connection.close() # send_codes

def test_compare(db_codes, url_codes):
    print("\ntype of db_codes:")
    for code in db_codes:
        print(type(code))

    print("\ntype of url_codes:")
    for url in url_codes:
        print(type(url))

    print("\ncomparing codes")
    for code in db_codes:
        for url in url_codes:
            if code == url:
                print(code)

    # test_compare

def run():
    db_port = os.getenv('DB_PORT')
    url_queue_name = os.getenv('URL_QUEUE_NAME')
    code_queue_name = os.getenv('CODE_QUEUE_NAME')

    urls = get_urls(url_queue_name)
    url_codes = get_codes_from_urls(urls)
    db_codes = get_codes_from_db(db_port)
    unique_codes = compare_code_lists(url_codes, db_codes)
    delete_deprecated_codes(db_codes, url_codes, db_port)
    send_codes(unique_codes, code_queue_name)
    # run

if __name__ == '__main__':
    run()