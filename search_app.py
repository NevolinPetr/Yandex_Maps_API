import pygame
import requests
import sys
import os
import math
from distance import lonlat_distance
from geo import reverse_geocode
from bis import find_business
from input_box import InputBox
from PIL import Image
LAT_STEP = 0.008
LON_STEP = 0.02
coord_to_geo_x = 0.0000428
coord_to_geo_y = 0.0000428


def ll(x, y):
    return "{0},{1}".format(x, y)


# Структура для хранения результатов поиска:
# координаты объекта, его название и почтовый индекс, если есть.

class SearchResult(object):
    def __init__(self, point, address, postal_code=None):
        self.point = point
        self.address = address
        self.postal_code = postal_code


# Параметры отображения карты:
# координаты, масштаб, найденные объекты и т.д.

class MapParams(object):
    def __init__(self):
        self.lat = 55.729738
        self.lon = 37.664777
        self.zoom = 15  # Масштаб карты на старте.
        self.type = "map"  # Тип карты на старте.
        self.search_result = None  # Найденный объект для отображения на карте.
        self.use_postal_code = False

    def ll(self):
        return ll(self.lon, self.lat)

    def update(self, event):
        if event.key == pygame.K_PAGEUP and self.zoom < 19:
            self.zoom += 1
        elif event.key == pygame.K_PAGEDOWN and self.zoom > 2:
            self.zoom -= 1
        elif event.key == pygame.K_LEFT:
            self.lon -= LON_STEP * math.pow(2, 15 - self.zoom)
        elif event.key == pygame.K_RIGHT:
            self.lon += LON_STEP * math.pow(2, 15 - self.zoom)
        elif event.key == pygame.K_UP and self.lat < 85:
            self.lat += LAT_STEP * math.pow(2, 15 - self.zoom)
        elif event.key == pygame.K_DOWN and self.lat > -85:
            self.lat -= LAT_STEP * math.pow(2, 15 - self.zoom)
        elif event.key == pygame.K_1:
            self.type = 'map'
        elif event.key == pygame.K_2:
            self.type = 'sat'
        elif event.key == pygame.K_3:
            self.type = 'sat,skl'
        elif event.key == pygame.K_DELETE:
            self.search_result = None
        elif event.key == pygame.K_INSERT:
            self.use_postal_code = not self.use_postal_code
        if self.lon > 180:
            self.lon -= 360
        if self.lon < -180:
            self.lon += 360

    def screen_to_geo(self, pos):
        dy = 225 - pos[1]
        dx = pos[0] - 300
        lx = self.lon + dx * coord_to_geo_x * math.pow(2, 15 - self.zoom)
        ly = self.lat + dy * coord_to_geo_y * math.cos(math.radians(self.lat)) * math.pow(2, 15 - self.zoom)
        return lx, ly

    def add_reverse_toponym_search(self, pos):
        point = self.screen_to_geo(pos)
        toponym = reverse_geocode(ll(point[0], point[1]))
        self.search_result = SearchResult(
            point,
            toponym["metaDataProperty"]["GeocoderMetaData"]["text"] if toponym else None,
            toponym["metaDataProperty"]["GeocoderMetaData"]["Address"].get("postal_code") if toponym else None)

    def add_reverse_org_search(self, pos):
        self.search_result = None
        point = self.screen_to_geo(pos)
        org = find_business(ll(point[0], point[1]))
        if not org:
            return
        org_point = org["geometry"]["coordinates"]
        org_lon = float(org_point[0])
        org_lat = float(org_point[1])
        if lonlat_distance((org_lon, org_lat), point) <= 50:
            self.search_result = SearchResult(point, org["properties"]["CompanyMetaData"]["name"])


def load_map(mp):
    map_request = f'http://static-maps.yandex.ru/1.x/?ll={mp.ll()}&z={mp.zoom}&l={mp.type}'
    if mp.search_result:
        map_request += f'&pt={mp.search_result.point[0]},{mp.search_result.point[1]},pm2grm'
    response = requests.get(map_request)
    if not response:
        print("Ошибка выполнения запроса:")
        print(map_request)
        print("Http статус:", response.status_code, "(", response.reason, ")")
        sys.exit(1)
    map_file = "map.png"
    try:
        with open(map_file, "wb") as file:
            file.write(response.content)
    except IOError as ex:
        print("Ошибка записи временного файла:", ex)
        sys.exit(2)
    return map_file


def render_text(text):
    font = pygame.font.Font(None, 30)
    return font.render(text, 1, (100, 0, 100))


def main():
    pygame.init()
    screen = pygame.display.set_mode((600, 450))
    mp = MapParams()
    input_box = InputBox(50, 10, 140, 32)
    im = Image.open('data/search_icon.png')
    im = im.resize((30, 30))
    im.save('data/search_icon.png')
    button = pygame.image.load('data/search_icon.png').convert_alpha()
    b_rect = pygame.Rect(10, 10, 50, 50)
    while True:
        event = pygame.event.wait()
        if event.type == pygame.QUIT:  # Выход из программы
            break
        elif event.type == pygame.KEYUP:  # Обрабатываем различные нажатые клавиши.
            mp.update(event)
        elif event.type == pygame.MOUSEBUTTONUP:  # Выполняем поиск по клику мышки.
            if event.button == 1:  # LEFT_MOUSE_BUTTON
                mp.add_reverse_toponym_search(event.pos)
                if b_rect.collidepoint(event.pos):
                    text = input_box.text
                    toponym = reverse_geocode(text)
                    if toponym:
                        point = toponym['Point']['pos'].split()
                        mp.lon = float(point[0])
                        mp.lat = float(point[1])
                        print(mp.lon, mp.lat)
                        mp.search_result = SearchResult(
                            point,
                            toponym["metaDataProperty"]["GeocoderMetaData"]["text"] if toponym else None,
                            toponym["metaDataProperty"]["GeocoderMetaData"]["Address"].get("postal_code")
                            if toponym else None)
                        print(toponym["metaDataProperty"]["GeocoderMetaData"]["text"],
                              toponym["metaDataProperty"]["GeocoderMetaData"]["Address"].get("postal_code"))
                    else:
                        input_box.text = 'Ничего не найдено'
            elif event.button == 3:  # RIGHT_MOUSE_BUTTON
                mp.add_reverse_org_search(event.pos)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN and input_box.active:
                text = input_box.text
                toponym = reverse_geocode(text)
                if toponym:
                    point = toponym['Point']['pos'].split()
                    mp.lon = float(point[0])
                    mp.lat = float(point[1])
                    print(mp.lon, mp.lat)
                    mp.search_result = SearchResult(
                        point,
                        toponym["metaDataProperty"]["GeocoderMetaData"]["text"] if toponym else None,
                        toponym["metaDataProperty"]["GeocoderMetaData"]["Address"].get("postal_code")
                        if toponym else None)
                    print(toponym["metaDataProperty"]["GeocoderMetaData"]["text"],
                          toponym["metaDataProperty"]["GeocoderMetaData"]["Address"].get("postal_code"))
                else:
                    input_box.text = 'Ничего не найдено'
        map_file = load_map(mp)
        screen.blit(pygame.image.load(map_file), (0, 0))
        if mp.search_result:
            if mp.use_postal_code and mp.search_result.postal_code:
                text = render_text(mp.search_result.postal_code + ", " + mp.search_result.address)
            else:
                text = render_text(mp.search_result.address)
            screen.blit(text, (20, 400))
        input_box.handle_event(event)
        input_box.update()
        input_box.draw(screen)
        screen.blit(button, b_rect)
        pygame.display.flip()
    pygame.quit()
    os.remove(map_file)


if __name__ == "__main__":
    main()
