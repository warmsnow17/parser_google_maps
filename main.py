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
    url = f"http://api.geonames.org/searchJSON?country={country}&featureCode=PPLA&maxRows=10&lang=ru&username={username}"
    response = requests.get(url)
    data = response.json()

    cities = []
    for city in data['geonames']:
        cities.append(city['name'])

    return cities


def search_places(api_key: str, query: str, location: str) -> list:
    username = os.getenv('GEONAMES_USERNAME')
    country_codes = ['RU']

    if location.upper() in country_codes:
        cities = get_largest_cities(location, username)
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
    raw_cities = input('Введите города через запятую: ')
    cities = raw_cities.split(',')
    return query, cities


def get_xlsx(query, cities):
    api_key = os.getenv('API_KEY')
    # query = "такси"
    # cities = [
    #     "Москва",
    #     "Санкт-Петербург",
    #     "Новосибирск",
    #     "Екатеринбург",
    #     "Нижний Новгород",
    #     "Казань",
    #     "Челябинск",
    #     "Омск",
    #     "Самара",
    #     "Ростов-на-Дону",
    #     "Уфа",
    #     "Красноярск",
    #     "Воронеж",
    #     "Пермь",
    #     "Волгоград",
    #     "Краснодар",
    #     "Калининград",
    #     "Владивосток"
    # ]

    results = search_places(api_key, query, cities)

    df = pd.DataFrame.from_dict(results)

    date = datetime.datetime.now()

    df.to_excel(f'{date}---{query}.xlsx')


if __name__ == '__main__':
    query, cities = get_cities_and_query()
    get_xlsx(query=query, cities=cities)
