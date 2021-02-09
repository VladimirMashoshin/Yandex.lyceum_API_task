import requests
import sys

# Запрос к static map api, возвращает изображение карты
# point - кортеж/список/строка с двумя координатами (центр карты)
# если оставить point пустым, вы обязаны указать точку на карте для автопозиционирования
# map_type - тип карты, по умолчанию "map"
# kwargs - можно передать любые нужные параметры (смотри документацию static yandex map api)
# в формате param=value, param2=value2,...


def map_request(point=None, map_type="map", **kwargs):
    url = "http://static-maps.yandex.ru/1.x/"
    params = kwargs
    if point:
        if isinstance(point, str):
            ll = point
        else:
            ll = ','.join(map(str, point))
        params['ll'] = ll
    params['l'] = map_type
    response = requests.get(url, params=params)
    if not response:
        print("Ошибка выполнения запроса:")
        print(url, params)
        print("Http статус:", response.status_code, "(", response.reason, ")")
        sys.exit(1)
    return response.content
