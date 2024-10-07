import os

import pika
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from browsermobproxy import Server
from colorama import Back, Style
import time
from dotenv import load_dotenv

load_dotenv('environment/crawl.env')

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
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'cmp-product-card-layout__list'))
        )

        if console_debug_on:
            print(Back.CYAN + "cmp-product-card-layout__list FOUND")
            print(Style.RESET_ALL)

        while True:
            ul_element = driver.find_element(By.CLASS_NAME, 'cmp-product-card-layout__list')
            buttons = ul_element.find_elements(By.CLASS_NAME, 'cmp-product-card__button')

            if not buttons:
                break

            if console_debug_on:
                print(Back.YELLOW + f"{len(buttons)} buttons FOUND")
                print(Style.RESET_ALL)

            for i in range(len(buttons)):
                try:

                    ul_element = driver.find_element(By.CLASS_NAME, 'cmp-product-card-layout__list')
                    buttons = ul_element.find_elements(By.CLASS_NAME, 'cmp-product-card__button')

                    if console_debug_on:
                        print(Back.MAGENTA + f"sub-button {i}")
                        print(Style.RESET_ALL)

                    button = buttons[i]
                    driver.execute_script("arguments[0].scrollIntoView();", button)
                    button.click()
                    time.sleep(2)

                    har = proxy.har

                    for entry in har['log']['entries']:
                        request_url = entry['request']['url']

                        if request_url.startswith("https://www.mcdonalds.com/dnaapp/itemList?country"):
                            if console_debug_on:
                                print(f"{request_url}")

                            if request_url not in input_url_list:
                                input_url_list.append(request_url)

                    driver.find_element(By.CLASS_NAME, 'cmp-product-card-layout__navigate-button').click()

                except Exception as e:
                    print(f"An error occurred while processing button: {e}")
                    continue
            break

    except Exception as e:
        print(f"An error occurred while locating the UL element: {e}")

    server.stop()
    driver.quit()
    return input_url_list # capture_request_urls

def run():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    queue_name = os.getenv('URL_QUEUE_NAME')
    channel.queue_declare(queue=queue_name, durable=True)

    start_url = "https://www.mcdonalds.com/no/nb-no/meny/nutrition-calculator.html"
    url_list = []
    url_list = capture_request_urls(start_url, url_list)

    print("\n\n#################################################\n\n")
    for url in url_list:
        channel.basic_publish(exchange='', routing_key=queue_name, body=url)

    connection.close()
    # run

if __name__ == "__main__":
    run()