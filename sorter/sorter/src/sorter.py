import json
import os

import requests
import pika
from urllib.request import urlopen
from dotenv import load_dotenv
from itertools import combinations

load_dotenv('environment/sorter.env')

# make groups of items that fit min(1 drink + >= 1 food)
# where the caloric count of a group is <= (calories +- (range/2))/meals per day
# M = min(1drink + >= 1food) where Mc <= (Di/Md)
# Mc = caloric content of a meal
# Di = calories +- range/2
# r = range
# c = calories
# md = meals per day
def make_meals(item_dict, r, c, md):
    drinks = [item for key, item in item_dict.items() if isinstance(item, dict) and item.get('foodType') == 'drink']
    foods = [item for key, item in item_dict.items() if isinstance(item, dict) and item.get('foodType') == 'food']

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
    meals = []
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
                    'total_calories': total_calories
                })

    return meals # make_meals


# combine meals into days

# add dates to days

# append menu plan to packet

# get items from queue
def get_items_from_queue(queue_name):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    channel.queue_declare(queue=queue_name, durable=True)

    items = ""

    method_frame, header_frame, body = channel.basic_get(queue=queue_name, auto_ack=True)

    if method_frame:
        items = body.decode('utf-8')

    connection.close()
    return json.loads(items) # get_items_from_queue

def run():
    queue_name = os.getenv('CODE_KCAL_QUEUE')
    items = get_items_from_queue(queue_name)
    print(items)  # Add this to see the structure of the items

    calories = items.get('calories')
    range = items.get('range')
    meals_per_day = items.get('mealsPerDay')
    days = items.get('days')

    meals = make_meals(items, range, calories, meals_per_day)


if __name__ == "__main__":
    run()
