import requests


# для справки смотри документацию по поиску организаций в API яндекс карт
def find_businesses(ll, spn, locale="ru_RU"):
    search_api_server = "https://search-maps.yandex.ru/v1/"
    api_key = "25701fd2-f16d-412e-8923-cda41906e414"  # вставить api_key
    search_params = {
        "apikey": api_key,
        "text": 'организация',
        "lang": locale,
        "ll": ll,
        "rspn": 1,
        "results": 5,
        "spn": spn,
        "type": "biz"
    }

    response = requests.get(search_api_server, params=search_params)
    if not response:
        raise RuntimeError(
            f"""Ошибка выполнения запроса:
            {search_api_server}
            Http статус: {response.status_code} ({response.reason})""")

    # Преобразуем ответ в json-объект
    json_response = response.json()
    # Получаем все найденные организации
    try:
        organizations = json_response["features"][0]
        point = organizations["properties"]["name"]
        return [point]
    except:
        return ['нет']


def find_business(ll, spn, locale="ru_RU"):
    orgs = find_businesses(ll, spn, locale=locale)
    if len(orgs):
        return orgs[0]
