import requests


# для справки смотри документацию по поиску организаций в API яндекс карт
def find_businesses(ll, spn, request, locale="ru_RU"):
    search_api_server = "https://search-maps.yandex.ru/v1/"
    api_key = "25701fd2-f16d-412e-8923-cda41906e414"  # вставить api_key
    search_params = {
        "apikey": api_key,
        "text": request,
        "lang": locale,
        "ll": ll,
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
    organizations = json_response["features"]
    return organizations


def find_business(ll, spn, request, locale="ru_RU"):
    orgs = find_businesses(ll, spn, request, locale=locale)
    if len(orgs):
        return orgs[0]
