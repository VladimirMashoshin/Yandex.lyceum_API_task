from maps.mapapi import map_request
from maps.geocoder import geocode, get_coordinates
import sys
import os
import pygame
import pygame_gui


class Map:
    def __init__(self, screen, manager, width, height):
        self.map_types = ['map', 'sat', 'sat,skl']
        self.map_type = 'map'
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
        self.show_postal_code = True
        self.last_postal_code = ""
        self.request()

    # создание интерфейса
    def init_ui(self):
        self.started = True
        manager, width, height = self.manager, self.width, self.height
        pygame_gui.elements.UILabel(relative_rect=pygame.Rect(0, 0, 100, 30), manager=manager, text="Координаты:")
        pygame_gui.elements.UILabel(relative_rect=pygame.Rect(0, 50, 100, 30), manager=manager, text="Масштаб:")
        pygame_gui.elements.UILabel(relative_rect=pygame.Rect(0, 100, 100, 30), manager=manager, text="Поиск:")
        pygame_gui.elements.UILabel(relative_rect=pygame.Rect(0, 150, 100, 30), manager=manager, text="Адрес:")
        pygame_gui.elements.UILabel(relative_rect=pygame.Rect(665, 450, 300, 30), manager=manager,
                                    text="Управление типом карты (кнопки):")
        pygame_gui.elements.UILabel(relative_rect=pygame.Rect(665, 500, 300, 30), manager=manager, text="1 - гибрид, 2 - спутник, 3 - схема")
        self.coords_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(110, 0, width * 3 / 4, height / 2),
            manager=manager)
        self.spn_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(110, 50, width * 3 / 4, height / 2),
            manager=manager)
        self.search_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(110, 100, width * 3 / 4, height / 2),
            manager=manager)
        self.address_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(110, 150, width * 3 / 4, height / 2),
            manager=manager)
        self.search_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((0, 200), (100, 40)),
                                                          text='Искать',
                                                          manager=manager)
        self.reset_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((150, 200), (250, 40)),
                                                         text='Сброс поискового результата',
                                                         manager=manager)
        self.postal_code_switch = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((450, 200), (300, 40)),
                                                               text="Скрыть почтовый индекс",
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
                 pygame.K_DOWN: self.move_down, pygame.K_1: self.change_to_hybrid, pygame.K_2: self.change_to_sputnik, pygame.K_3: self.change_to_scheme}
        if move not in moves:
            return
        if move in [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN]:
            long, lat = self.params['ll']
            long_spn, lat_spn = self.params['spn']
            new_long, new_lat = moves[move](long, lat, long_spn, lat_spn)
            self.params['ll'] = new_long, new_lat
            self.update_ui()
            self.request()
        else:
            self.params['l'] = moves[move]()
            self.update_ui()
            self.request()

    def change_to_hybrid(self):
        return self.map_types[2]

    def change_to_sputnik(self):
        return self.map_types[1]

    def change_to_scheme(self):
        return self.map_types[0]

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
        new_params, address, postal_code = get_coordinates(self.search_input.text)
        if new_params is None:
            print("Заданного места к сожалению не найдено!")
        else:
            self.params['ll'] = new_params
            self.last_postal_code = postal_code
            if self.cnt_flags == 100:
                self.flags.pop(0)
            else:
                self.cnt_flags += 1
            new_params = [str(coord) for coord in new_params]
            self.flags.append(",".join(new_params))
            if self.show_postal_code:
                address = address + ", Почтовый индекс: " + self.last_postal_code
            self.address_input.set_text(address)
        self.update_ui()
        self.request()

    # дисперчер обработки нажатия клавиш пользователем
    def on_key_pressed(self, key):
        valid_actions = {pygame.K_PAGEUP: self.scale_up, pygame.K_PAGEDOWN: self.scale_down,
                         pygame.K_LEFT: self.move, pygame.K_RIGHT: self.move, pygame.K_UP: self.move,
                         pygame.K_DOWN: self.move, pygame.K_1: self.move, pygame.K_2: self.move, pygame.K_3: self.move}
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
                    self.params["ll"] = self.started_params["ll"]
                    self.params["spn"] = self.started_params["spn"]
                    self.search_input.text = ""
                    self.address_input.text = ""
                    self.last_postal_code = ""
                    self.update_ui()
                    self.request()
                if event.ui_element == self.postal_code_switch:
                    if self.show_postal_code:
                        self.show_postal_code = False
                        self.postal_code_switch.set_text("Показать почтовый индекс")
                        full_address = self.address_input.text.split(", Почтовый индекс: ")
                        self.address_input.set_text(full_address[0])
                    else:
                        self.show_postal_code = True
                        self.postal_code_switch.set_text("Скрыть почтовый индекс")
                        if self.last_postal_code:
                            self.address_input.set_text(self.address_input.text + ", Почтовый индекс: " + self.last_postal_code)
        elif event.type == pygame.KEYUP:
            self.on_key_pressed(event.key)

    # отрисовка класса (в данный момент только отрисовывает карту)
    def draw(self):
        if self.info_loaded:
            self.screen.blit(pygame.image.load(self.map_file), (0, 250))

    def __del__(self):
        if os.path.isfile(self.map_file):
            os.remove(self.map_file)
