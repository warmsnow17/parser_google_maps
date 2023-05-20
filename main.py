import json
import os
import requests
import googlemaps
from dotenv import load_dotenv
from loguru import logger
import pandas as pd
import datetime

from tqdm import tqdm


load_dotenv()


def get_largest_cities(country, username):
    url = f"http://api.geonames.org/searchJSON?country={country}&featureCode=PPLA&maxRows=2&lang=ru&username={username}"
    logger.warning(url)
    response = requests.get(url)
    print(response.status_code)
    data = response.json()

    cities = []
    for city in data['geonames']:
        cities.append(city['name'])

    return cities


def search_places(api_key: str, query: str, location: str) -> list:
    username = os.getenv('GEONAMES_USERNAME')
    with open('countries.json', 'r', encoding='utf-8') as file:
        country_codes = json.load(file)

    logger.warning(country_codes)
    if location.capitalize() in country_codes:
        cities = get_largest_cities(country_codes[location.capitalize()],
                                    username)
    else:
        cities = [location]

    client = googlemaps.Client(key=api_key)
    final_result = []

    for city in tqdm(cities, desc="Processing cities"):
        places_result = client.places(f"{query} {city}", language='ru')

        for place in tqdm(places_result['results']):
            place_id = place['place_id']
            details = client.place(place_id, language='ru')

            raw_time = details['result'].get('opening_hours')
            if raw_time is not None:
                work_hour = ''
                work_hour_list = raw_time.get('weekday_text')
                for line in work_hour_list:
                    work_hour += f'\n{line}'
            else:
                work_hour = ''

            result = {
                "ID": place_id,
                "Название": details['result'].get('name'),
                "Адрес": details['result'].get('formatted_address'),
                "Телефон": details['result'].get('formatted_phone_number'),
                "Сайт": details['result'].get('website'),
                "Время работы": work_hour,
                "Широта": details['result']['geometry']['location'].get('lat'),
                "Долгота": details['result']['geometry']['location'].get('lng'),
            }

            final_result.append(result)

    return final_result


def get_cities_and_query():
    query = input('Введите ваш запрос: ').lower()
    location = input('Введите страну: ')
    return query, location


def get_xlsx(query, location):
    api_key = os.getenv('API_KEY')

    results = search_places(api_key, query, location)

    df = pd.DataFrame.from_dict(results)

    date = datetime.datetime.timestamp(datetime.datetime.now())

    df.to_excel(f'{date}---{query}.xlsx')


if __name__ == '__main__':
    query, location = get_cities_and_query()
    get_xlsx(query=query, location=location)
