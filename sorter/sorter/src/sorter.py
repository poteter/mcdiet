import json
import os

import requests
import pika
from urllib.request import urlopen
from dotenv import load_dotenv
from itertools import combinations

load_dotenv('environment/formatter.env')

# make groups of items that fit min(1 drink + >= 1 food)
# where the caloric count of a group is <= (calories +- (range/2))/meals per day
# M = min(1drink + >= 1food) where Mc <= (Di/Md)
# Mc = caloric content of a meal
# Di = calories +- range/2
# r = range
# c = calories
# md = meals per day
def make_meals(item_list, r, c, md):
    drinks = [item for item in item_list if item['type'] == 'drink']
    foods = [item for item in item_list if item['type'] == 'food']

    if not drinks:
        print("No drinks available.")
        return []
    if not foods:
        print("No foods available.")
        return []

    Di_max = c + (r / 2)

    Mc_max = Di_max / md

    food_combinations = []
    for i in range(1, len(foods) + 1):
        food_combinations.extend(combinations(foods, i))

    # Generate meals by pairing each drink with food combinations
    meals = []
    for drink in drinks:
        drink_calories = drink['calories']
        if drink_calories > Mc_max:
            continue
        for food_combo in food_combinations:
            food_calories = sum(item['calories'] for item in food_combo)
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


def run():
    print('sorter') # run


if __name__ == "__main__":
    run()
