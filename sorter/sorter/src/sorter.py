import json
import os
from datetime import date

import requests
import pika
from urllib.request import urlopen
from dotenv import load_dotenv
from itertools import combinations
import random

load_dotenv('environment/sorter.env')

# M  = min(1drink + >= 1food) where Mc <= (Di/Md)
# Mc = caloric content of a meal
# Di = calories +- range/2 = daily caloric intake
# r  = range
# c  = calories
# md = meals per day
# make groups of items that fit min(1 drink + >= 1 food)
# where the caloric count of a group is <= (calories +- (range/2))/meals per day
def make_meals(item_dict, r, c, md):
    drinks = [item for key, item in item_dict.items() if isinstance(item, dict) and item.get('foodType') == 'drink']
    foods = [item for key, item in item_dict.items() if isinstance(item, dict) and item.get('foodType') == 'food']
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
                    'total_calories': total_calories
                })

    return meals # make_meals

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
        i = 0

        while i < meals_per_day:
            temp_day['meal'] = random.choice(meals)

        total_calories = sum(temp_day['total_calories'])

        if Di_min <= total_calories <= Di_max:
            current_date = date.today()
            temp_day['date'] = current_date.strftime('%m/%d/%Y')
            days_list.append(temp_day)

    return days # make_days

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
    print(items)

    calories = items.get('calories')
    range = items.get('range')
    Di_max = calories + (range / 2)
    Di_min = calories - (range / 2)
    days = items.get('days')

    meals_per_day = items.get('mealsPerDay')
    meals = make_meals(items, range, calories, meals_per_day)
    print(type(meals))
    i = 0
    for meal in meals:
        if i < 10:
            print(meal)
            i += 1
        else:
            break
    calendar_days = make_days(meals, days, meals_per_day, Di_min, Di_max)
    print(type(calendar_days))
    i = 0
    for day in calendar_days:
        if i < 10:
            print(day)
            i += 1
        else:
            break

if __name__ == "__main__":
    run()
