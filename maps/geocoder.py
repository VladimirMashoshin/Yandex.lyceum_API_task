import requests

API_KEY = '40d1649f-0493-4b70-98ba-98533de7710b'


def geocode(address=None, ll=None):
    # Собираем запрос для геокодера.
    if address:
        geoc = address
    else:
        geoc = ll
    geocoder_request = f"http://geocode-maps.yandex.ru/1.x/"
    geocoder_params = {
        "apikey": API_KEY,
        "geocode": geoc,
        "format": "json"}

    # Выполняем запрос.
    response = requests.get(geocoder_request, params=geocoder_params)
    if response:
        # Преобразуем ответ в json-объект
        json_response = response.json()
    else:
        raise RuntimeError(
            f"""Ошибка выполнения запроса:
            {geocoder_request}
            Http статус: {response.status_code} ({response.reason})""")
    # Получаем первый топоним из ответа геокодера.
    # Согласно описанию ответа он находится по следующему пути:
    features = json_response["response"]["GeoObjectCollection"]["featureMember"]
    if len(features) == 0:
        return None, None
    components = json_response["response"]["GeoObjectCollection"]["featureMember"][0]
    components = components["GeoObject"]["metaDataProperty"]["GeocoderMetaData"]["Address"]
    if "postal_code" in components:
        postal_code = components["postal_code"]
    else:
        postal_code = "не найден"
    components = components["Components"]
    full_adress = ""
    for i in range(len(components)):
        full_adress += components[i]["name"]
        if (i != len(components) - 1):
            full_adress += ", "
    if features:
        return features[0]["GeoObject"], full_adress, postal_code
    else:
        return None, None, None


# Получаем координаты объекта по его адресу и его полный адрес с почтовым индексом.
def get_coordinates(address):
    toponym, full_address, postal_code = geocode(address, None)
    if not toponym:
        # raise NotADirectoryError("Такого места не существует!")
        return None, None, None

    # Координаты центра топонима:
    toponym_coordinates = toponym["Point"]["pos"]
    # Широта, преобразованная в плавающее число:
    toponym_longitude, toponym_lattitude = toponym_coordinates.split(" ")
    return (float(toponym_longitude), float(toponym_lattitude)), full_address, postal_code


# Получаем параметры объекта для рисования карты вокруг него.
def get_ll_span(address):
    toponym = geocode(address, None)
    if not toponym:
        return None, None

    # Координаты центра топонима:
    toponym_coodrinates = toponym["Point"]["pos"]
    # Долгота и Широта :
    toponym_longitude, toponym_lattitude = toponym_coodrinates.split(" ")

    # Собираем координаты в параметр ll
    ll = ",".join([toponym_longitude, toponym_lattitude])

    # Рамка вокруг объекта:
    envelope = toponym["boundedBy"]["Envelope"]

    # левая, нижняя, правая и верхняя границы из координат углов:
    l, b = envelope["lowerCorner"].split(" ")
    r, t = envelope["upperCorner"].split(" ")

    # Вычисляем полуразмеры по вертикали и горизонтали
    dx = abs(float(l) - float(r)) / 2.0
    dy = abs(float(t) - float(b)) / 2.0

    # Собираем размеры в параметр span
    span = f"{dx},{dy}"

    return ll, span


# Находим ближайшие к заданной точке объекты заданного типа.
# kind - тип объекта
def get_nearest_object(point, kind):
    ll = f"{point[0]},{point[1]}"
    geocoder_request = f"http://geocode-maps.yandex.ru/1.x/"
    geocoder_params = {
        "apikey": API_KEY,
        "geocode": ll,
        "format": "json"}
    if kind:
        geocoder_params['kind'] = kind
    # Выполняем запрос к геокодеру, анализируем ответ.
    response = requests.get(geocoder_request, params=geocoder_params)
    if not response:
        raise RuntimeError(
            f"""Ошибка выполнения запроса:
            {geocoder_request}
            Http статус: {response.status_code,} ({response.reason})""")

    # Преобразуем ответ в json-объект
    json_response = response.json()

    # Получаем первый топоним из ответа геокодера.
    features = json_response["response"]["GeoObjectCollection"]["featureMember"]
    if features:
        return features[0]["GeoObject"]["name"]
    else:
        return None
