import json
import os
import time
from typing import Tuple

import requests
import googlemaps
from dotenv import load_dotenv
from loguru import logger
import pandas as pd
import datetime

from tqdm import tqdm

load_dotenv()


def get_language_choice() -> str:
    language = input('Введите язык для выдачи результатов (например, "en" для английского, "ru" для русского и т.д.): ')
    return language


def get_largest_cities(country: str, username: str, number_cities: int) -> list:
    url = f"http://api.geonames.org/searchJSON?country={country}&featureCode=PPLA&maxRows={number_cities}&lang=ru&username={username}"
    logger.warning(url)
    response = requests.get(url)
    data = response.json()

    cities = []
    for city in data['geonames']:
        cities.append(city['name'])

    return cities


def search_places(api_key: str, query: str, location: str, number_cities: int, language: str, districts: list) -> list:
    username = os.getenv('GEONAMES_USERNAME')
    with open('countries.json', 'r', encoding='utf-8') as file:
        country_codes = json.load(file)

    logger.warning(country_codes)
    if location.capitalize() in country_codes:
        cities = get_largest_cities(country_codes[location.capitalize()],
                                    username, number_cities)
    else:
        cities = [location]

    client = googlemaps.Client(key=api_key)
    final_result = []

    for city in tqdm(cities, desc="Processing cities"):
        for district in districts or ['']:
            places_result = client.places(f"{query} {city} {district}", language=language)

            while places_result:
                for place in tqdm(places_result['results']):
                    place_id = place['place_id']
                    details = client.place(place_id, language=language)

                    raw_time = details['result'].get('opening_hours')
                    if raw_time is not None:
                        work_hour = ''
                        work_hour_list = raw_time.get('weekday_text')
                        for line in work_hour_list:
                            work_hour += f'\n{line}'
                    else:
                        work_hour = ''

                    # получить полный адрес
                    full_address = details['result'].get('formatted_address')
                    # разделить адрес на компоненты
                    address_components = client.geocode(full_address)[0]['address_components']

                    country, region, city, address, postal_code = "", "", "", "", ""
                    for component in address_components:
                        if 'country' in component['types']:
                            country = component['long_name']
                        elif 'administrative_area_level_1' in component['types']:
                            region = component['long_name']
                        elif 'locality' in component['types']:
                            city = component['long_name']
                        elif 'route' in component['types']:
                            address = component['long_name']
                        elif 'postal_code' in component['types']:
                            postal_code = component['long_name']

                    result = {
                        "ID": place_id,
                        "Название": details['result'].get('name'),
                        "Страна": country,
                        "Регион": region,
                        "Город": city,
                        "Адрес": address,
                        "Индекс": postal_code,
                        "Телефон": details['result'].get('formatted_phone_number'),
                        "Сайт": details['result'].get('website'),
                        "Время работы": work_hour,
                        "Широта": details['result']['geometry']['location'].get('lat'),
                        "Долгота": details['result']['geometry']['location'].get('lng'),
                    }

                    final_result.append(result)

                next_page_token = places_result.get('next_page_token')

                if next_page_token:
                    time.sleep(1)
                    places_result = client.places(f"{query} {city}", language='ru', page_token=next_page_token)
                else:
                    places_result = None

    return final_result


def get_cities_and_query() -> Tuple[int, str, list, list]:
    number_cities = int(input(
        'Если в запросе вы выбираете страну, настройте количество городов для выдачи (например напишите число 10): '))
    query = input('Введите ваш запрос: ').lower()
    location_input = input('Введите страну или город через запятую: ')
    locations = [location.strip() for location in location_input.split(',')]
    district_input = input('Введите районы через запятую (оставьте пустым, если не хотите использовать районы): ')
    districts = [district.strip() for district in district_input.split(',')] if district_input else []

    return number_cities, query, locations, districts



def get_xlsx(number_cities:int, query: str, locations: list, language: str, districts: list) -> None:
    api_key = os.getenv('API_KEY')

    results = []
    for location in locations:
        results.extend(search_places(api_key, query, location, number_cities, language, districts))

    df = pd.DataFrame.from_dict(results)

    date = datetime.datetime.now().strftime('%H:%M_%d-%m-%Y')

    df.to_excel(f'{date}---{query}.xlsx', engine='openpyxl', index=False)


if __name__ == '__main__':
    number_cities, query, locations, districts = get_cities_and_query()
    language = get_language_choice()
    get_xlsx(number_cities=number_cities, query=query, locations=locations, language=language, districts=districts)
