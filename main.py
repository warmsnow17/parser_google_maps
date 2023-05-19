import os

import googlemaps
from dotenv import load_dotenv
import pandas as pd
import datetime
load_dotenv()


def search_places(api_key: str, query: str, cities: list) -> list:
    client = googlemaps.Client(key=api_key)
    final_result = []

    for city in cities:
        places_result = client.places(f"{query} {city}")

        for place in places_result['results']:
            place_id = place['place_id']
            details = client.place(place_id)

            result = {
                "ID": place_id,
                "Название": details['result'].get('name'),
                "Адрес": details['result'].get('formatted_address'),
                "Телефон": details['result'].get('formatted_phone_number'),
                "Сайт": details['result'].get('website'),
                "Время работы": details['result'].get('opening_hours'),
                "Широта": details['result']['geometry']['location'].get('lat'),
                "Долгота": details['result']['geometry']['location'].get('lng'),
            }

            final_result.append(result)

    return final_result


api_key = os.getenv('API_KEY')
query = "такси"
cities = [
    "Москва",
    "Санкт-Петербург",
    "Новосибирск",
    "Екатеринбург",
    "Нижний Новгород",
    "Казань",
    "Челябинск",
    "Омск",
    "Самара",
    "Ростов-на-Дону",
    "Уфа",
    "Красноярск",
    "Воронеж",
    "Пермь",
    "Волгоград",
    "Краснодар",
    "Калининград",
    "Владивосток"
]

results = search_places(api_key, query, cities)

df = pd.DataFrame.from_dict(results)

date = datetime.datetime.now()

df.to_excel(f'{date}{query}.xlsx')
