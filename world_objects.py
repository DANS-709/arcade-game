import time
import random
import arcade
import math
from collections import deque

ENEMY_MOVE_SPEED = 15  # Скорость анимации врагов (пикселей за кадр)
# Параметры по умолчанию
EXTEND_PARAMS = {
    'hp': 'max_hp',
    'moves_left': 'moves_count',
    'damage_deal': '0',
    'view_range': '4',
    'move_range': '5'
}


class Entity(arcade.Sprite):
    def __init__(self, filename, role, stats_dict):
        super().__init__(filename)
        self.width = 100
        self.height = 120
        self.role = role
        self.stats_dict = stats_dict
        self.set_full_stats()
        self.active_effects = []

        # Анимация движения
        self.path_queue = deque()  # Очередь координат (px, py) куда идти
        self.is_moving = False

    def __setitem__(self, key, value):
        self.stats_dict[key] = value

    def __getitem__(self, item):
        return self.stats_dict[item]

    def get_stat(self, stat_name):
        base = self.stats_dict.get(stat_name, 0)
        bonus = 0
        for effect in self.active_effects:
            if effect['stat'] == stat_name:
                bonus += effect['value']
        bonus += self.stats_dict.get(f'temporary_{stat_name}', 0)
        return base + bonus

    def get_as_dict(self):
        res = {}
        for key in self.stats_dict:
            res[key] = self.get_stat(key)
        res['role'] = self.role
        return res

    def set_full_stats(self):
        for param1, param2 in EXTEND_PARAMS.items():
            if param2.isdigit():
                self.stats_dict[param1] = int(param2)
            else:
                self.stats_dict[param1] = self.stats_dict.get(param2, 0)

    def add_effect(self, stat, value, duration):
        self.active_effects.append({
            'stat': stat, 'value': value, 'duration': duration
        })


    def update_effects_turn(self):
        surviving_effects = []
        for effect in self.active_effects:
            effect['duration'] -= 1
            if effect['duration'] > 0:
                surviving_effects.append(effect)
        self.active_effects = surviving_effects
        keys_to_reset = [k for k in self.stats_dict if k.startswith('temporary_')]
        for k in keys_to_reset:
            self.stats_dict[k] = 0

    def update_position(self):
        """ Плавное перемещение по очереди путей """
        if not self.path_queue:
            self.is_moving = False
            return

        self.is_moving = True
        target_x, target_y = self.path_queue[0]

        # Вектор движения
        dx = target_x - self.center_x
        dy = target_y - self.center_y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        if distance < ENEMY_MOVE_SPEED:
            # Пришли в точку
            self.center_x = target_x
            self.center_y = target_y
            self.path_queue.popleft()
        else:
            # Двигаемся
            angle = math.atan2(dy, dx)
            self.center_x += math.cos(angle) * ENEMY_MOVE_SPEED
            self.center_y += math.sin(angle) * ENEMY_MOVE_SPEED


class Lair(arcade.Sprite):
    """ Класс Логова Чудища """

    def __init__(self, position):
        try:
            super().__init__("images/lair.png", scale=1)
        except:
            super().__init__()
            self.texture = arcade.make_circle_texture(50, arcade.color.DARK_RED)

        self.position = position
        self.guardians_spawned = False
        self.guardians_needed = 6
        self.last_spawn_time = time.time()
        self.next_spawn_interval = random.randint(40, 90)