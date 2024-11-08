import json
import os
import signal
import sys
import threading
import traceback
import time
import logging

import pika
from pika import exceptions
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from browsermobproxy import Server
from dotenv import load_dotenv
from selenium.common.exceptions import StaleElementReferenceException, ElementClickInterceptedException

# variable to switch between docker and local run mode
local_mode = False

# Global flag for graceful shutdown
shutdown_flag = threading.Event()

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
if local_mode:
    proxy_path = os.environ.get('BROWSERMOB_PROXY_PATH',
                                'browsermob-proxy-2.1.4-bin/browsermob-proxy-2.1.4/bin/browsermob-proxy')
else:
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

if local_mode:
    service = ChromeService(executable_path="/usr/local/bin/chromedriver")
else:
    service = ChromeService(executable_path="/usr/local/bin/chromedriver")

driver = webdriver.Chrome(service=service, options=chrome_options)

# Set to True to enable console debug messages
console_debug_on = False

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

def send_to_rabbit(url_list, rabbitmq_host, rabbitmq_port, rabbitmq_username, rabbitmq_password, url_queue):
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
        for url in url_list:
            message = json.dumps(url)
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

def run_crawl_sequence(mc_url, rabbitmq_host, rabbitmq_port, rabbitmq_username, rabbitmq_password, url_queue):
    url_list = []
    url_list = capture_request_urls(mc_url, url_list)
    logging.info(f"url_list: {url_list}")
    send_to_rabbit(url_list, rabbitmq_host, rabbitmq_port, rabbitmq_username, rabbitmq_password, url_queue)

class ThreadConsumeRabbit(threading.Thread):
    def __init__(self,
                 exchange_name,
                 exchange_type,
                 queue_name,
                 callback,
                 rabbit_host,
                 rabbit_port,
                 rabbit_username,
                 rabbit_password,
                 mc_url):
        super().__init__()
        self.exchange_name = exchange_name
        self.exchange_type = exchange_type
        self.queue_name = queue_name
        self.callback = callback
        self.rabbit_host = rabbit_host
        self.rabbit_port = rabbit_port
        self.rabbit_username = rabbit_username
        self.rabbit_password = rabbit_password
        self.mc_url = mc_url
        self.connection = None
        self.channel = None

    def run(self):
        try:
            credentials = pika.PlainCredentials(self.rabbit_username, self.rabbit_password)
            parameters = pika.ConnectionParameters(
                host=self.rabbit_host,
                port=self.rabbit_port,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )

            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()

            # Declare the exchange
            self.channel.exchange_declare(exchange=self.exchange_name, exchange_type=self.exchange_type, durable=True)

            # Declare a temporary queue with a unique name
            result = self.channel.queue_declare(queue='', exclusive=True)
            temp_queue = result.method.queue

            # Bind the temporary queue to the exchange
            self.channel.queue_bind(exchange=self.exchange_name, queue=temp_queue)

            logging.info(f"Waiting for messages in exchange '{self.exchange_name}'")

            # Start consuming
            self.channel.basic_consume(
                queue=temp_queue,
                on_message_callback=self.on_message,
                auto_ack=True
            )

            # Start consuming in a loop
            while not shutdown_flag.is_set():
                self.connection.process_data_events(time_limit=1)

        except pika.exceptions.AMQPConnectionError as e:
            logging.error(f"Connection error: {e}")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
        finally:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                logging.info("RabbitMQ connection closed.")

    def on_message(self, ch, method, properties, body):
        message = body.decode()
        logging.info(f"Received message: {message}")
        if message.strip().lower() == "run":
            logging.info("Received 'run' command. Triggering run_crawl_sequence().")
            run_crawl_sequence(self.mc_url, self.rabbit_host, self.rabbit_port, self.rabbit_username, self.rabbit_password, self.queue_name)

    def stop(self):
        if self.channel:
            self.channel.stop_consuming()
        if self.connection and not self.connection.is_closed:
            self.connection.close()

def graceful_shutdown(signum, frame):
    logging.info(f"Received signal {signum}. Shutting down gracefully...")
    shutdown_flag.set()

def main():
    path_flag_docker = True
    if path_flag_docker:
        load_dotenv('/app/environment/crawl.env')
    else:
        load_dotenv('../environment/crawl.env')

    # RabbitMQ Configuration for Consumer
    exchange_name = os.getenv('FANOUT_EXCHANGE_NAME', 'runTriggerFanoutExchange')
    exchange_type = 'fanout'

    # RabbitMQ Configuration for Publisher
    url_queue_name = os.getenv('URL_QUEUE_NAME', 'mcURL')

    # RabbitMQ general configuration
    rabbitmq_host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
    rabbitmq_port = int(os.getenv('RABBITMQ_PORT', 5672))
    rabbitmq_username = os.getenv('RABBITMQ_USERNAME', 'admin')
    rabbitmq_password = os.getenv('RABBITMQ_PASSWORD', 'admin')

    # McDonald's product catalog URLs
    mc_url = os.getenv('MCDONALDS_URL')
    logging.info(f"MCDONALDS_URL: {mc_url}")

    # Signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)

    # Initialize and start the RabbitMQ consumer thread
    consumer = ThreadConsumeRabbit(
        exchange_name=exchange_name,
        exchange_type=exchange_type,
        queue_name=url_queue_name,
        callback=run_crawl_sequence,
        rabbit_host=rabbitmq_host,
        rabbit_port=rabbitmq_port,
        rabbit_username=rabbitmq_username,
        rabbit_password=rabbitmq_password,
        mc_url=mc_url
    )

    consumer.start()

    # Wait for shutdown flag
    try:
        while not shutdown_flag.is_set():
            shutdown_flag.wait(timeout=1)
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt received.")
    finally:
        consumer.stop()
        consumer.join()
        logging.info("Application has been shut down gracefully.")


if __name__ == '__main__':
    main()