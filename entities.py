import arcade
import time
import random
import math
import base64
import io
from collections import deque
from constants import *
from game_logic import apply_ability
from PIL import Image

class Entity(arcade.Sprite):
    def __init__(self, filename=None, role="enemy", stats_dict=None, json_data=None):
        # Если есть json_data, пытаемся загрузить картинку из base64, иначе filename
        if json_data and "image_b64" in json_data and json_data["image_b64"]:
            try:
                img_data = base64.b64decode(json_data["image_b64"])
                image = Image.open(io.BytesIO(img_data))
                texture = arcade.Texture(name=json_data.get("name", "unknown"), image=image)
                super().__init__(texture=texture)
            except Exception as e:
                print(f"Ошибка загрузки картинки из JSON: {e}")
                super().__init__(filename or "images/hero_1.jpg")
        else:
            super().__init__(filename or "images/hero_1.jpg")
        self.width = 100
        self.height = 120
        self.role = role
        self.stats_dict = stats_dict if stats_dict else {}
        self.active_effects = []
        self.abilities = []
        # Если загружаем из JSON
        if json_data:
            self.load_from_json(json_data)
        self.set_full_stats()
        if self.abilities:
            self.selected_ability = self.abilities[0].get('effect', "target['hp'] -= 5; buff(hero, 'hp', 2, 2)")
        else:
            self.selected_ability = "target['hp'] -= 5; buff(hero, 'hp', 2, 2)"
        # Анимация движения
        self.path_queue = deque()
        self.is_moving = False

    def load_from_json(self, data):
        """ Инициализация на основе JSON """
        self.name = data.get("name", "Unknown")

        # Базовые статы из JSON
        self.stats_dict = {
            'max_hp': data.get("hp", 10),
            'level': data.get("level", 1),
        }
        # Добавляем атрибуты stats (str, dex...)
        if "stats" in data:
            self.stats_dict.update(data["stats"])

        self.set_full_stats()  # Заполняем дефолтные значения (armor, defense и т.д.)
        # Контекст для скриптов расы и класса
        # Мы позволяем скрипту менять self.stats_dict через переменную 'hero'
        context = {
            'hero': self.stats_dict,
            'buff': lambda t, s, v, d: self.add_effect(s, v, d)  # Упрощенный бафф на себя при создании
        }

        # Применяем Race Script
        if 'race' in data:
            for cmd in data["race"].split(';'):
                apply_ability(self, self, cmd)

        # Применяем Class Script
        if "class" in data:
            for cmd in data["class"].split(';'):
                apply_ability(self, self, cmd)

        # Загружаем способности
        if "abilities" in data:
            self.abilities = data["abilities"]

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
        return (base + bonus, bonus, base)

    def get_as_dict(self):
        res = {}
        for key in self.stats_dict:
            res[key] = self.get_stat(key)[0]
        res['role'] = self.role
        return res

    def set_full_stats(self):
        for param1, param2 in EXTEND_PARAMS.items():
            if param1 in self.stats_dict:
                continue
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
        # Очистка старых
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

        dx = target_x - self.center_x
        dy = target_y - self.center_y
        distance = (dx ** 2 + dy ** 2) ** 0.5

        if distance < ENEMY_MOVE_SPEED:
            self.center_x = target_x
            self.center_y = target_y
            self.path_queue.popleft()
        else:
            angle = 0
            # Избегаем деления на ноль
            if distance > 0:
                angle = math.atan2(dy, dx)
            self.center_x += math.cos(angle) * ENEMY_MOVE_SPEED
            self.center_y += math.sin(angle) * ENEMY_MOVE_SPEED

    def receive_damage(self, raw_damage):
        """ Расчет получения урона с учетом брони и защиты """
        armor = self.get_stat('armor')[0]
        defense_percent = self.get_stat('defense')[0]

        # 1. Процентное снижение
        reduced_damage = raw_damage * (1 - defense_percent / 100)

        # 2. Плоское снижение (не меньше 1 урона, если удар был сильным)
        final_damage = max(0, reduced_damage - armor)

        self.stats_dict['hp'] -= final_damage
        return final_damage


class Lair(arcade.Sprite):
    """ Класс Логова Чудища """

    def __init__(self, position):
        try:
            super().__init__("images/lair.png")
            self.width, self.height = TILE_SIZE, TILE_SIZE
        except:
            super().__init__()
            self.texture = arcade.make_circle_texture(50, arcade.color.DARK_RED)

        self.position = position
        self.guardians_spawned = False
        self.guardians_needed = 6
        self.last_spawn_time = time.time()
        self.next_spawn_interval = random.randint(40, 90)
