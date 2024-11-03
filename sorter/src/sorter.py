import json
import logging
import os
import signal
import sys
import threading
import time
from datetime import date, timedelta
import requests
from pika import exceptions
import pika
from dotenv import load_dotenv
from itertools import combinations
import random

load_dotenv('../environment/sorter.env')

# global flag
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

# M  = min(1drink + >= 1food) where Mc <= (Di/Md)
# Mc = caloric content of a meal
# Di = calories +- range/2 = daily caloric intake
# r  = range
# c  = calories
# md = meals per day
# make groups of items that fit min(1 drink + >= 1 food)
# where the caloric count of a group is <= (calories +- (range/2))/meals per day
def make_meals(item_dict, r, c, md):
    drinks = [
        {**item, 'item_id': key}
        for key, item in item_dict.items()
        if isinstance(item, dict) and item.get('foodType') == 'drink'
    ]
    foods = [
        {**item, 'item_id': key}
        for key, item in item_dict.items()
        if isinstance(item, dict) and item.get('foodType') == 'food'
    ]
    meals = []

    if not drinks:
        print("No drinks available.")
        return []
    if not foods:
        print("No foods available.")
        return []

    Di_max = c + (r / 2)
    Mc_max = Di_max / md

    food_combinations = []
    for i in range(1, min(4, len(foods) + 1)):
        food_combinations.extend(combinations(foods, i))

    # Generate meals by pairing each drink with food combinations
    for drink in drinks:
        drink_calories = drink['energyKcal']
        if drink_calories > Mc_max:
            continue
        for food_combo in food_combinations:
            food_calories = sum(item['energyKcal'] for item in food_combo)
            total_calories = drink_calories + food_calories
            if total_calories <= Mc_max:
                meal_items = [drink] + list(food_combo)
                meals.append({
                    'items': meal_items,
                    'total_calories_meal': total_calories
                })

    return meals  # make_meals


# meals         = list of meals from make_meals
# days          = number of days diet plan spans
# meals_per_day = number of meals in a day
# Di_min        = minimum of daily caloric intake = calories - (range / 2)
# Di_max        = maximum of daily caloric intake = calories + (range / 2)
# combine meals into days of eating, where the number of meals in a
# day of eating = meals_per_day, and a day of eating
# should have a caloric count within the range of Di_min and Di_max.
def make_days(meals, days, meals_per_day, Di_min, Di_max):
    days_list = []
    while len(days_list) < days:
        temp_day = {}
        day_meals = []
        total_calories = 0
        i = 0

        while i <= meals_per_day:
            meal = random.choice(meals)
            day_meals.append(meal)
            total_calories += meal['total_calories_meal']
            i += 1

        if Di_min <= total_calories <= Di_max:
            current_date = date.today() + timedelta(days=len(days_list))
            temp_day['date'] = current_date.strftime('%m/%d/%Y')
            temp_day['meals'] = day_meals
            temp_day['total_calories_day'] = total_calories
            days_list.append(temp_day)

    return days_list  # make_days


# append menu plan to packet
def append_plan_to_packet(user, calories, range, days, meals_per_day, calendar_days):
    db_packet = {'user': user,
                 'calories': calories,
                 'range': range,
                 'days': days,
                 'meals_per_day': meals_per_day,
                 'plan': calendar_days}
    return db_packet # append_plan_to_packet

def send_to_db(packet, api_url):
    if packet:
        try:
            response = requests.post(api_url, json=packet)

            if response.status_code == 200:
                logging.info("Successfully sent data to the API.")
                logging.info(f"Status code: {response.status_code}")
            else:
                logging.error(f"Failed to send data. Status code: {response.status_code}")
            logging.error(f"Response: {response.text}")

        except requests.exceptions.RequestException as e:
            logging.error(f"An error occurred: {e}")
    else:
        logging.info("empty json")
    # send_data

def graceful_shutdown(signal, frame):
    shutdown_flag.set()
    logging.info(f"Signal {signal} received. Shutting down.")

def on_message(ch, method, properties, body, param, args):
    api_url = args
    items = body.decode('utf-8')

    calories = items.get('calories')
    range = items.get('range')
    Di_max = calories + (range / 2)
    Di_min = calories - (range / 2)
    days = items.get('days')
    user = items.get('user')

    meals_per_day = items.get('mealsPerDay')
    meals = make_meals(items, range, calories, meals_per_day)

    calendar_days = make_days(meals, days, meals_per_day, Di_min, Di_max)

    db_packet = append_plan_to_packet(user, calories, range, days, meals_per_day, calendar_days)
    send_to_db(db_packet, api_url)
    # on_message

def run_consumer(queue_name, api_url):
    if not queue_name:
        logging.error("One or more required environment variables are missing. Exiting.")
        sys.exit(1)

    try:
        # Establish connection
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()

        # Declare the parameter queue
        channel.queue_declare(queue=queue_name, durable=True)

        # Define the callback with additional arguments
        channel.basic_consume(
            queue=queue_name,
            on_message_callback=lambda ch, method, properties, body, param, args: on_message(
                ch, method, properties, body, args, api_url
            ),
            auto_ack=True
        )

        logging.info(f"waiting for message from {queue_name}")

        # Start consuming in a separate thread to allow graceful shutdown
        consume_thread = threading.Thread(target=channel.start_consuming)
        consume_thread.start()

        while not shutdown_flag.is_set():
            time.sleep(1)

        channel.stop_consuming()
        consume_thread.join()
        connection.close()
        logging.info("RabbitMQ consumer has been shut down gracefully.")
    except pika.exceptions.AMQPConnectionError as e:
        logging.error(f"AMQP connection error: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
    # run_consumer

def run():
    queue_name = os.getenv('CODE_KCAL_QUEUE')
    db_port = os.getenv('DB_PORT')
    api_url = f"http://localhost:{db_port}/api/item"

    # signal handlers
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)

    logging.info("Starting RabbitMQ consumer.")
    run_consumer(queue_name, api_url)
    logging.info("Consumer stopped.")
    # run

if __name__ == "__main__":
    run()
