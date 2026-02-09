import arcade
import time
import random
import math
import base64
from io import BytesIO
from collections import deque
from constants import *
from game_logic import apply_ability
from PIL import Image


class Entity(arcade.Sprite):
    def __init__(self, filename=None, role="enemy", stats_dict=None, json_data=None):
        self.image_path = filename or "images/hero_1.jpg"
        # Если есть json_data, пытаемся загрузить картинку
        if json_data and "image_b64" in json_data and json_data["image_b64"]:
            try:
                img_data = base64.b64decode(json_data["image_b64"])
                image = Image.open(BytesIO(img_data))
                image = image.convert('RGBA')
                self.image_path = f'images/{json_data.get("name", "unknown")}.png'
                image.save(self.image_path, 'png')
                texture = arcade.Texture(image)
                super().__init__(texture)
            except Exception as e:
                print(f"Ошибка загрузки картинки из JSON: {e}")
                super().__init__(filename or "images/hero_1.jpg")
        else:
            super().__init__(filename or "images/hero_1.jpg")

        self.width = 120
        self.height = 120
        self.role = role
        # Приоритет: явно переданный словарь (например из сохранения) > json > дефолт
        self.stats_dict = stats_dict if stats_dict else {}
        self.active_effects = []
        self.abilities = []
        self.anim_phase = None  # "forward", "back", None
        self.anim_start_pos = None
        self.anim_timer = 0
        self.anim_duration = 0.2  # Длительность одной фазы в секундах
        self.inventory = []

        # Анимация тряски (Урон)
        self.shake_timer = 0

        # Флаг для загрузки сохранения (чтобы не сбрасывать HP)
        is_loaded_from_save = stats_dict is not None and 'hp' in stats_dict

        if json_data:
            self.load_from_json(json_data, skip_stats=is_loaded_from_save)

        self.set_full_stats()

        self.selected_ability = None

        self.path_queue = deque()
        self.is_moving = False

    def load_from_json(self, data, skip_stats=False):
        """ Инициализация на основе JSON """
        self.name = data.get("name", "Unknown")

        if not skip_stats:
            self.stats_dict = {
                'max_hp': data.get("hp", 10),
                'level': data.get("level", 1),
            }
            if "stats" in data:
                self.stats_dict.update(data["stats"])

        self.set_full_stats()


        # Применяем Race/Class только если это новая игра (не из сохранения)
        if not skip_stats:
            if 'race' in data:
                try:
                    self.race = data['race']
                    apply_ability(self, self, self.race[1])
                except:
                    pass

            if "class" in data:
                try:
                    self.cls = data['class']
                    apply_ability(self, self, self.cls[1])
                except:
                    pass

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

    def equip_item(self, item):
        """ Применение статов и способностей предмета """
        # 1. Суммируем статы
        for stat, value in item.stats_dict.items():
            current_val = self.stats_dict.get(stat, 0)
            self.stats_dict[stat] = current_val + value
            self.inventory.append(item)

        # 2. Добавляем способности
        if item.abilities:
            self.abilities.extend(item.abilities)

        print(f"{self.name} купил {item.name}!")


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
            if distance > 0:
                angle = math.atan2(dy, dx)
            self.center_x += math.cos(angle) * ENEMY_MOVE_SPEED
            self.center_y += math.sin(angle) * ENEMY_MOVE_SPEED

    def start_attack_animation(self, target_pos):
        """ Запускает рывок в сторону цели """
        if not self.anim_phase:
            self.anim_phase = "forward"
            self.anim_start_pos = (self.center_x, self.center_y)
            self.anim_timer = 0

            # Вычисляем точку рывка (на 30% расстояния до цели)
            dx = target_pos[0] - self.center_x
            dy = target_pos[1] - self.center_y
            self.anim_target_lunge = (self.center_x + dx * 0.3, self.center_y + dy * 0.3)

    def start_shake(self, duration=0.2):
        """ Запускает тряску спрайта """
        self.orig_x = self.center_x
        self.orig_y = self.center_y
        self.shake_timer = duration

    def update_animation_logic(self, delta_time):
        """ Обновляет логику смещений (вызывать в update) """
        # Логика рывка
        if self.anim_phase:
            self.anim_timer += delta_time
            t = min(self.anim_timer / self.anim_duration, 1.0)

            if self.anim_phase == "forward":
                # Летим вперед
                self.center_x = arcade.math.lerp(self.anim_start_pos[0], self.anim_target_lunge[0], t)
                self.center_y = arcade.math.lerp(self.anim_start_pos[1], self.anim_target_lunge[1], t)
                if t >= 1.0:
                    self.anim_phase = "back"
                    self.anim_timer = 0
            elif self.anim_phase == "back":
                # Возвращаемся
                self.center_x = arcade.math.lerp(self.anim_target_lunge[0], self.anim_start_pos[0], t)
                self.center_y = arcade.math.lerp(self.anim_target_lunge[1], self.anim_start_pos[1], t)
                if t >= 1.0:
                    self.anim_phase = None
                    self.center_x, self.center_y = self.anim_start_pos
        # Логика тряски (Shake)
        if self.shake_timer > 0:
            self.center_x += random.uniform(-2, 2)
            self.center_y += random.uniform(-2, 2)
            self.shake_timer -= delta_time
            if self.shake_timer < 0:
                self.center_x = self.orig_x
                self.center_y = self.orig_y

class NPC(arcade.Sprite):
    def __init__(self, npc_data, x, y, scale):
        self.name = npc_data.get("name", "NPC")
        self.phrases = npc_data.get("phrases", [])
        self.final_phrases = npc_data.get("final_phrases", [])
        self.quests = npc_data.get("quests", [])

        self.image_path = npc_data.get("image", "images/npc.png")
        try:
            super().__init__(self.image_path)
        except:
            super().__init__()
            self.color = arcade.color.GRAY

        self.width, self.height = 29 * scale, 29 * scale
        self.center_x = x
        self.center_y = y
        self.time_to_new_phrase = 5
        self.time = 0
        # Поля для совместимости с CharacterInfoOverlay
        self.role = "npc"
        self.stats_dict = {}
        self.active_effects = []
        self.abilities = [{'name': quest['type'],
                          'effect': " ; ".join(['coins:' + str(quest['reward_coins']),
                                                'rep:' + str(quest['reward_rep'])]),
                          'description': quest['text']} for quest in npc_data['quests']]

    def get_random_phrase(self, game_view=None, delta_time=0):
        if not self.phrases:
            return ""
        self.time += delta_time
        if game_view and not delta_time:
            return random.choice(self.final_phrases)
        if game_view and game_view.final_quest_unlocked:
            if self.final_phrases:
                return random.choice(self.final_phrases)
        if not delta_time:
            return random.choice(self.phrases)
        elif self.time > self.time_to_new_phrase:
            self.time = 0
            return random.choice(self.phrases)
        return ""

    def get_random_quest(self):
        if not self.quests:
            return None
        return random.choice(self.quests)

class ShopItem(arcade.Sprite):
    """ Предмет, который можно купить """

    def __init__(self, item_data, x, y, scale):
        # item_data - это словарь с параметрами предмета
        self.name = item_data.get("name", "Unknown Item")
        self.image_path = item_data.get("image", "images/potion.png")

        try:
            super().__init__(self.image_path)
        except:
            super().__init__()
            self.color = arcade.color.GOLD
        self.width, self.height = 29 * scale, 29 * scale

        self.center_x = x
        self.center_y = y
        self.price = item_data.get("price", 100)

        # Статы, которые дает предмет
        self.stats_dict = item_data.get("stats", {})
        # Способности, которые дает предмет
        self.abilities = item_data.get("abilities", [])

        # Поля для совместимости с CharacterInfoOverlay
        self.role = "item"
        self.active_effects = []

    def get_stat(self, stat_name):
        """ Возвращает (value, buff, base) для UI """
        val = self.stats_dict.get(stat_name, 0)
        return (val, 0, val)

class Lair(arcade.Sprite):
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
        self.spawn_interval = [2, 3]
        self.last_spawn_time = time.time()
        self.next_spawn_interval = random.randint(*self.spawn_interval)