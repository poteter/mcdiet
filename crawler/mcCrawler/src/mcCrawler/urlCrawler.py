import json
import os
import pika
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from browsermobproxy import Server
import time
from dotenv import load_dotenv
import logging
import signal
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

load_dotenv('environment/crawl.env')

# rabbitMQ Configuration
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
RABBITMQ_USERNAME = os.getenv('RABBITMQ_USERNAME', 'guest')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'guest')
COMMAND_QUEUE = os.getenv('COMMAND_QUEUE_NAME', 'crawl_commands')
URL_QUEUE = os.getenv('URL_QUEUE_NAME', 'crawl_results')

MCDONALDS_URL = os.getenv('MCDONALDS_URL')

proxy_path = 'browsermob-proxy-2.1.4-bin\\browsermob-proxy-2.1.4\\bin\\browsermob-proxy'  # Update with the path to your BrowserMob Proxy executable
server = Server(proxy_path)
server.start()
proxy = server.create_proxy()

chrome_options = Options()
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--ignore-ssl-errors')
chrome_options.add_argument('--allow-running-insecure-content')
chrome_options.add_argument('--disable-features=IsolateOrigins,site-per-process')
chrome_options.add_argument('--disable-extensions')
chrome_options.add_argument('--disable-popup-blocking')
chrome_options.add_argument(f"--proxy-server={proxy.proxy}")
chrome_options.add_argument("--headless=old")
chrome_options.add_argument('--disable-gpu')

service = ChromeService(executable_path="chromedriver.exe")
driver = webdriver.Chrome(service=service, options=chrome_options)

console_debug_on = False

def capture_request_urls(start_url, input_url_list):
    proxy.new_har("capture_requests", options={'captureHeaders': True})
    driver.get(start_url)
    time.sleep(5)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'cmp-product-card-layout__list'))
        )

        if console_debug_on:
            logging.info("cmp-product-card-layout__list FOUND")

        while True:
            ul_element = driver.find_element(By.CLASS_NAME, 'cmp-product-card-layout__list')
            buttons = ul_element.find_elements(By.CLASS_NAME, 'cmp-product-card__button')

            if not buttons:
                break

            if console_debug_on:
                logging.info(f"{len(buttons)} buttons FOUND")

            for i in range(len(buttons)):
                try:
                    ul_element = driver.find_element(By.CLASS_NAME, 'cmp-product-card-layout__list')
                    buttons = ul_element.find_elements(By.CLASS_NAME, 'cmp-product-card__button')

                    if console_debug_on:
                        logging.info(f"sub-button {i}")

                    button = buttons[i]
                    driver.execute_script("arguments[0].scrollIntoView();", button)
                    button.click()
                    time.sleep(2)

                    har = proxy.har

                    for entry in har['log']['entries']:
                        request_url = entry['request']['url']

                        if request_url.startswith("https://www.mcdonalds.com/dnaapp/itemList?country"):
                            if console_debug_on:
                                logging.info(f"{request_url}")

                            if request_url not in input_url_list:
                                input_url_list.append(request_url)

                    driver.find_element(By.CLASS_NAME, 'cmp-product-card-layout__navigate-button').click()

                except Exception as e:
                    logging.error(f"An error occurred while processing button: {e}")
                    continue
            break

    except Exception as e:
        logging.error(f"An error occurred while locating the UL element: {e}")

    server.stop()
    driver.quit()
    return input_url_list # capture_request_urls

def send_to_rabbit(url_list):
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USERNAME, RABBITMQ_PASSWORD)
        parameters = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            credentials=credentials
        )

        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.queue_declare(queue=URL_QUEUE, durable=True)
        message = json.dumps(url_list)
        channel.basic_publish(
            exchange='',
            routing_key=URL_QUEUE,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,
            ))

        logging.info(f"Sent {len(url_list)} URLs to queue '{URL_QUEUE}'")

    except Exception as e:
        logging.error(f"Failed to send URLs to RabbitMQ: {e}")
    finally:
        if 'connection' in locals() and connection.is_open:
            connection.close() # send_to_rabbit

def on_message(ch, method, body):
    message = body.decode('utf-8')
    logging.info(f"Received message: {message}")

    if message.strip().lower() == "run":
        logging.info("Starting crawler(s)")
        url_list = []
        url_list = capture_request_urls(MCDONALDS_URL, url_list)
        send_to_rabbit(url_list)
        logging.info("Crawl process completed.")
    else:
        logging.warning(f"Unknown command received: {message}")

    ch.basic_ack(delivery_tag=method.delivery_tag) # on_message

def start_consumer():
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USERNAME, RABBITMQ_PASSWORD)
        parameters = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            credentials=credentials
        )

        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.queue_declare(queue=COMMAND_QUEUE, durable=True)
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue=COMMAND_QUEUE, on_message_callback=on_message)

        logging.info(f"Waiting for messages in queue '{COMMAND_QUEUE}'. To exit press CTRL+C")
        channel.start_consuming()

    except Exception as e:
        logging.error(f"Error in RabbitMQ consumer: {e}")
    finally:
        if 'connection' in locals() and connection.is_open:
            connection.close() # start_consumer

def graceful_shutdown(sig, frame):
    logging.info("Shutting down gracefully...")
    try:
        server.stop()
        driver.quit()
    except Exception as e:
        logging.error(f"Error during shutdown: {e}")
    sys.exit(0) # graceful_shutdown

def run():
    # signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)

    start_consumer() # run

if __name__ == "__main__":
    run()