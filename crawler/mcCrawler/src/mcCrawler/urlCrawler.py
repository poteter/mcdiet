import json
import os
import signal
import sys
import traceback
import time
import logging

import pika
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from browsermobproxy import Server
from colorama import Back, Style
from dotenv import load_dotenv
from selenium.common.exceptions import StaleElementReferenceException, ElementClickInterceptedException

# Load environment variables
load_dotenv('/app/environment/crawl.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("server.log")
    ]
)

# Fetch environment variables for Browsermob-Proxy
proxy_path = os.environ.get('BROWSERMOB_PROXY_PATH',
                            '/app/browsermob-proxy-2.1.4-bin/browsermob-proxy-2.1.4/bin/browsermob-proxy')
server = Server(proxy_path)
server.start()
proxy = server.create_proxy()

# Configure Chrome options
chrome_options = Options()
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--ignore-ssl-errors')
chrome_options.add_argument('--allow-running-insecure-content')
chrome_options.add_argument('--disable-features=IsolateOrigins,site-per-process')
chrome_options.add_argument('--disable-extensions')
chrome_options.add_argument('--disable-popup-blocking')
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument(f"--proxy-server={proxy.proxy}")
chrome_options.add_argument("--headless")  # Updated headless option
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument('--window-size=1920,1080')  # Ensure enough window size
chrome_options.add_argument('--disable-blink-features=AutomationControlled')  # Helps avoid detection
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")  # Set a common user-agent

# Optionally, disable images and CSS to speed up loading
chrome_prefs = {
    "profile.managed_default_content_settings.images": 2,
    "profile.managed_default_content_settings.stylesheets": 2
}
chrome_options.add_experimental_option("prefs", chrome_prefs)

service = ChromeService(executable_path="/usr/local/bin/chromedriver")
driver = webdriver.Chrome(service=service, options=chrome_options)

# Set to True to enable console debug messages
console_debug_on = False

mcdonalds_url = os.getenv('MCDONALDS_URL')

def capture_request_urls(start_url, input_url_list, max_retries=3):
    proxy.new_har("capture_requests", options={'captureHeaders': True})
    driver.get(start_url)
    time.sleep(5)  # Initial wait for the page to load

    try:
        # Wait for the product list to be present
        product_list = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'cmp-product-card-layout__list'))
        )
        logging.info("Found the product card layout list.")
    except Exception as e:
        driver.save_screenshot("product_list_error.png")
        logging.error(f"An error occurred while locating the UL element: {e}")
        logging.error(traceback.format_exc())
        return input_url_list

    try:
        # Find all buttons within the product list
        buttons = product_list.find_elements(By.CLASS_NAME, 'cmp-product-card__button')
        total_buttons = len(buttons)
        logging.info(f"Found {total_buttons} buttons.")
    except Exception as e:
        driver.save_screenshot("buttons_finding_error.png")
        logging.error(f"An error occurred while finding buttons: {e}")
        logging.error(traceback.format_exc())
        return input_url_list

    for i in range(total_buttons):
        retries = 0
        while retries < max_retries:
            try:
                # Re-fetch the product list and buttons each time to avoid stale references
                product_list = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'cmp-product-card-layout__list'))
                )
                buttons = product_list.find_elements(By.CLASS_NAME, 'cmp-product-card__button')

                if i >= len(buttons):
                    logging.warning(f"Button {i + 1} not found. Total buttons available: {len(buttons)}")
                    break

                button = buttons[i]

                # Scroll the button into view
                driver.execute_script("arguments[0].scrollIntoView();", button)
                time.sleep(1)  # Allow scrolling to complete

                # Click the button
                button.click()
                logging.info(f"Clicked button {i + 1}/{total_buttons}.")
                time.sleep(2)  # Wait for actions after clicking

                # Get HAR data
                har = proxy.har

                for entry in har['log']['entries']:
                    request_url = entry['request']['url']

                    if request_url.startswith("https://www.mcdonalds.com/dnaapp/itemList?country"):
                        if console_debug_on:
                            logging.info(f"Captured URL: {request_url}")

                        if request_url not in input_url_list:
                            input_url_list.append(request_url)

                # Attempt to click the navigate button
                try:
                    navigate_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CLASS_NAME, 'cmp-product-card-layout__navigate-button'))
                    )
                    navigate_button.click()
                    logging.info("Clicked navigate button.")
                    time.sleep(2)  # Wait for the page to navigate back or update
                except Exception as e:
                    driver.save_screenshot("navigate_button_error.png")
                    logging.error(f"An error occurred while locating/clicking the navigate button: {e}")
                    logging.error(traceback.format_exc())
                    # Decide whether to continue or break
                    break

                # If everything succeeded, break out of the retry loop
                break

            except StaleElementReferenceException as e:
                retries += 1
                logging.warning(f"StaleElementReferenceException encountered for button {i + 1}. "
                                f"Retrying {retries}/{max_retries}...")
                time.sleep(1)  # Wait before retrying
                if retries == max_retries:
                    driver.save_screenshot(f"button_{i + 1}_stale_error.png")
                    logging.error(f"Failed to process button {i + 1} after {max_retries} retries.")
            except ElementClickInterceptedException as e:
                retries += 1
                logging.warning(f"ElementClickInterceptedException encountered for button {i + 1}. "
                                f"Retrying {retries}/{max_retries}...")
                time.sleep(1)  # Wait before retrying
                if retries == max_retries:
                    driver.save_screenshot(f"button_{i + 1}_click_intercept_error.png")
                    logging.error(f"Failed to click button {i + 1} after {max_retries} retries.")
            except Exception as e:
                retries += 1
                logging.error(f"An unexpected error occurred while processing button {i + 1}: {e}")
                logging.error(traceback.format_exc())
                driver.save_screenshot(f"button_{i + 1}_unexpected_error.png")
                break  # Skip to the next button

    return input_url_list  # capture_request_urls

def send_to_rabbit(url_list):
    # rabbitMQ Configuration
    rabbitmq_host = os.getenv('RABBITMQ_HOST', 'localhost')
    rabbitmq_port = int(os.getenv('RABBITMQ_PORT', 5672))
    rabbitmq_username = os.getenv('RABBITMQ_USERNAME', 'guest')
    rabbitmq_password = os.getenv('RABBITMQ_PASSWORD', 'guest')
    command_queue = os.getenv('COMMAND_QUEUE_NAME', 'crawl_commands')
    url_queue = os.getenv('URL_QUEUE_NAME', 'crawl_results')

    try:
        credentials = pika.PlainCredentials(rabbitmq_username, rabbitmq_password)
        parameters = pika.ConnectionParameters(
            host=rabbitmq_host,
            port=rabbitmq_port,
            credentials=credentials
        )

        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.queue_declare(queue=url_queue, durable=True)
        message = json.dumps(url_list)
        channel.basic_publish(
            exchange='',
            routing_key=url_queue,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,
            ))

        logging.info(f"Sent {len(url_list)} URLs to queue '{url_queue}'")

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
        url_list = capture_request_urls(mcdonalds_url, url_list)
        send_to_rabbit(url_list)
        logging.info("Crawl process completed.")
    else:
        logging.warning(f"Unknown command received: {message}")

    ch.basic_ack(delivery_tag=method.delivery_tag) # on_message

def start_consumer(rabbitmq_username, rabbitmq_password, rabbitmq_host, rabbitmq_port, command_queue):
    try:
        credentials = pika.PlainCredentials(rabbitmq_username, rabbitmq_password)
        parameters = pika.ConnectionParameters(
            host=rabbitmq_host,
            port=rabbitmq_port,
            credentials=credentials
        )

        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.queue_declare(queue=command_queue, durable=True)
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue=command_queue, on_message_callback=on_message)

        logging.info(f"Waiting for messages in queue '{command_queue}'. To exit press CTRL+C")
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

    # rabbitMQ Configuration
    rabbitmq_host = os.getenv('RABBITMQ_HOST', 'localhost')
    rabbitmq_port = int(os.getenv('RABBITMQ_PORT', 5672))
    rabbitmq_username = os.getenv('RABBITMQ_USERNAME', 'guest')
    rabbitmq_password = os.getenv('RABBITMQ_PASSWORD', 'guest')
    command_queue = os.getenv('COMMAND_QUEUE_NAME', 'crawl_commands')

    start_consumer(rabbitmq_username, rabbitmq_password, rabbitmq_host, rabbitmq_port, command_queue) # run

if __name__ == "__main__":
    run()