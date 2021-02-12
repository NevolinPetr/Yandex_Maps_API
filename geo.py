import requests


def reverse_geocode(ll):
    apikey = '40d1649f-0493-4b70-98ba-98533de7710b'
    geocoder_request_template = f'http://geocode-maps.yandex.ru/1.x/?apikey={apikey}&geocode={ll}&format=json'
    geocoder_request = geocoder_request_template.format(**locals())
    response = requests.get(geocoder_request)
    if not response:
        raise RuntimeError(
            f"""Ошибка выполнения запроса:
            {geocoder_request}
            Http статус: {response.status_code} ({response.reason})"""
        )
    json_response = response.json()
    features = json_response["response"]["GeoObjectCollection"]["featureMember"]
    return features[0]["GeoObject"] if features else None
