from maps.mapapi import map_request
from maps.geocoder import geocode, get_coordinates
import sys
import os
import pygame
import pygame_gui


class Map:
    def __init__(self, screen, manager, width, height):
        self.screen = screen
        self.manager = manager
        self.width = width
        self.height = height
        self.started_params = {'ll': (36.192640, 51.730894), 'spn': (0.05, 0.05)}
        self.params = {'ll': (36.192640, 51.730894), 'spn': (0.05, 0.05), 'l': 'map'}
        self.map_file = "map.png"
        self.info_loaded = False
        self.flags = []
        self.cnt_flags = 0
        self.request()

    # создание интерфейса
    def init_ui(self):
        manager, width, height = self.manager, self.width, self.height
        pygame_gui.elements.UILabel(relative_rect=pygame.Rect(0, 0, 100, 30), manager=manager, text="Координаты:")
        pygame_gui.elements.UILabel(relative_rect=pygame.Rect(0, 50, 100, 30), manager=manager, text="Масштаб:")
        pygame_gui.elements.UILabel(relative_rect=pygame.Rect(0, 100, 100, 30), manager=manager, text="Поиск:")

        self.coords_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(110, 0, width / 2, height / 2),
            manager=manager)
        self.spn_input = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect(110, 50, width / 2, height / 2),
                                                             manager=manager)
        self.search_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(110, 100, width / 2, height / 2),
            manager=manager)

        self.search_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((0, 150), (100, 40)),
                                                          text='Искать',
                                                          manager=manager)
        self.reset_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((300, 150), (400, 40)),
                                                         text='Сброс поискового результата',
                                                         manager=manager)
        self.update_ui()

    # служебный метод - преобразует координаты вида (10.2345,10.23456) в строку '10.2345,10.23456'
    def coord_to_string(self, coord):
        return ','.join(map(str, coord))

    # служебный метод - преобразует координаты из строки '10.2345,10.23456'  в кортеж (10.2345,10.23456)

    def string_to_coord(self, string):
        return tuple(map(float, string.split(',')))

    # движения (перемещения карты влево-вправо-вниз-вверх при нажатии стрелок на клавиатуре)
    # вся предобработка и постобработка выполняется в методе move,
    # методы move_right и и прочие move методы только рассчитывают новые координаты
    def move(self, move):
        moves = {pygame.K_LEFT: self.move_left, pygame.K_RIGHT: self.move_right, pygame.K_UP: self.move_up,
                 pygame.K_DOWN: self.move_down}
        if move not in moves:
            return
        long, lat = self.params['ll']
        long_spn, lat_spn = self.params['spn']
        new_long, new_lat = moves[move](long, lat, long_spn, lat_spn)
        self.params['ll'] = new_long, new_lat
        self.update_ui()
        self.request()

    def move_right(self, long, lat, long_spn, lat_spn):
        new_long = long + long_spn * 2
        return new_long, lat

    def move_left(self, long, lat, long_spn, lat_spn):
        new_long = long - long_spn * 2
        return new_long, lat

    def move_up(self, long, lat, long_spn, lat_spn):
        new_lat = lat + lat_spn
        return long, new_lat

    def move_down(self, long, lat, long_spn, lat_spn):
        new_lat = lat - lat_spn
        return long, new_lat

    # клавиша page_up - приблизим карту

    def scale_up(self, key=None):
        k = 2
        self.params['spn'] = tuple(map(lambda x: x / k, self.params['spn']))
        self.update_ui()
        self.request()

    # клавиша page_down - отдалим карту

    def scale_down(self, key=None):
        k = 2
        self.params['spn'] = tuple(map(lambda x: x * k, self.params['spn']))
        self.update_ui()
        self.request()

    # из параметров в self.params заполняем поля в интерфейсе
    def update_ui(self):
        self.coords_input.set_text(self.coord_to_string(self.params['ll']))
        self.spn_input.set_text(self.coord_to_string(self.params['spn']))

    # из полей в интерфейсе заполняем данные в self.params
    def update_data(self):
        self.params['ll'] = self.string_to_coord(self.coords_input.get_text())
        self.params['spn'] = self.string_to_coord(self.spn_input.get_text())

    # совершает запрос в API и обновляет карту
    def request(self):
        spn = self.coord_to_string(self.params['spn'])
        ll = self.coord_to_string(self.params['ll'])
        image = map_request(ll, self.params['l'], spn=spn, flags=self.flags)
        self.update_map(image)

    # обновление файла с картой

    def update_map(self, image):
        try:
            with open(self.map_file, "wb") as file:
                file.write(image)
        except IOError as ex:
            print("Ошибка записи временного файла:", ex)
            sys.exit(2)
        self.info_loaded = True

    # действие при нажатии  кнопки поиска
    def on_search(self):
        new_params = get_coordinates(self.search_input.text)
        # print(new_params)
        if new_params[0] is None and new_params[1] is None:
            print("Заданного места к сожалению не найдено!")
        else:
            self.params['ll'] = new_params
            if self.cnt_flags == 100:
                self.flags.pop(0)
            else:
                self.cnt_flags += 1
            new_params = [str(coord) for coord in new_params]
            self.flags.append(",".join(new_params))
        self.update_ui()
        self.request()

    # дисперчер обработки нажатия клавиш пользователем
    def on_key_pressed(self, key):
        valid_actions = {pygame.K_PAGEUP: self.scale_up, pygame.K_PAGEDOWN: self.scale_down,
                         pygame.K_LEFT: self.move, pygame.K_RIGHT: self.move, pygame.K_UP: self.move,
                         pygame.K_DOWN: self.move}
        if key in valid_actions:
            valid_actions[key](key)

    # диспетчер обработки всех действий
    def on_event(self, event):
        if event.type == pygame.USEREVENT:
            if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == self.search_button:
                    self.on_search()
                if event.ui_element == self.reset_button:
                    self.flags = []
                    self.cnt_flags = 0
                    self.params['ll'] = self.started_params['ll']
                    self.params['spn'] = self.started_params['spn']
                    self.search_input.text = ''
                    self.update_ui()
                    self.request()
        elif event.type == pygame.KEYUP:
            self.on_key_pressed(event.key)

    # отрисовка класса (в данный момент только отрисовывает карту)
    def draw(self):
        if self.info_loaded:
            self.screen.blit(pygame.image.load(self.map_file), (0, 200))

    def __del__(self):
        if os.path.isfile(self.map_file):
            os.remove(self.map_file)
