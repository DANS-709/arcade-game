import arcade
import random
import math
from perlin_noise import PerlinNoise

# --- КОНСТАНТЫ ---
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800
SCREEN_TITLE = "D&D Arcade Prototype"

TILE_SIZE = 100  # Размер клетки
GRID_WIDTH = 20  # Ширина карты в клетках
GRID_HEIGHT = 20  # Высота карты в клетках

# Типы местности
TERRAIN_MEADOW = 1
TERRAIN_FOREST = 2
TERRAIN_TOWN = 3
TERRAIN_BAR = 4
# Словарь соответствия: какой параметр инициализировать каким значением
EXTEND_PARAMS = {'hp': 'max_hp', 'moves_left': 'moves_count', 'damage_deal': '0'}


class Entity(arcade.Sprite):
    """ Базовый класс для Героя и Врагов """

    def __init__(self, filename, role, stats_dict):
        super().__init__(filename, scale=1)
        self.role = role
        self.stats_dict = stats_dict
        self.set_full_stats()
        self.temp_stats = dict()
        # Инициализируем временные бонусы нулями
        for key in list(self.stats_dict.keys()):
            self.temp_stats[f'temporary_{key}'] = 0

    def __setitem__(self, key, value):
        self.stats_dict[key] = value

    def __getitem__(self, item):
        return self.stats_dict[item]

    def get_stat(self, stat_name):
        """ Возвращает базу + временный бонус """
        base = self.stats_dict.get(stat_name, 0)
        bonus = self.temp_stats.get(f'temporary_{stat_name}', 0)
        return base + bonus

    def get_as_dict(self):
        """ Возвращает словарь текущих честных значений (база + бонусы) """
        res = {}
        for key in self.stats_dict:
            res[key] = self.get_stat(key)
        return res

    def set_full_stats(self):
        for param1, param2 in EXTEND_PARAMS.items():
            self.stats_dict[param1] = self.stats_dict.get(param2, 0)

    def reset_temp_stats(self):
        """ Очистка всех временных эффектов """
        for key in self.temp_stats:
            self.temp_stats[key] = 0


class MyGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        self.tile_list = None
        self.entity_list = None
        self.hero = None
        self.camera = None
        self.enemy_list = None
        self.selected_unit = None

        arcade.set_background_color(arcade.color.BLACK)

    def setup(self):
        self.tile_list = arcade.SpriteList()
        self.entity_list = arcade.SpriteList()
        self.enemy_list = arcade.SpriteList()

        self.camera = arcade.camera.Camera2D()

        noise = PerlinNoise(octaves=3)
        bar_locations = []

        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                n = noise([x / GRID_WIDTH, y / GRID_HEIGHT])
                tile_type = "meadow"
                img_file = "images/meadow.jpg"
                if n < -0.15:
                    img_file = "images/forest.jpg"
                    tile_type = "forest"
                elif n > 0.2:
                    img_file = "images/town.jpg"
                    tile_type = "town"
                    if random.random() < 0.1:
                        img_file = "images/bar.jpg"
                        tile_type = "bar"

                tile = arcade.Sprite(img_file)
                tile.width = TILE_SIZE
                tile.height = TILE_SIZE
                tile.center_x = x * TILE_SIZE + TILE_SIZE / 2
                tile.center_y = y * TILE_SIZE + TILE_SIZE / 2
                tile.properties = {'type': tile_type, 'grid_x': x, 'grid_y': y}
                self.tile_list.append(tile)
                if tile_type == "bar":
                    bar_locations.append(tile)
                    tile.color = arcade.color.GOLD

        hero_stats = {
            'max_hp': 99,
            'move_range': 3,
            'moves_count': 3,
            'damage_deal': 10
        }
        start_tile = random.choice(bar_locations) if bar_locations else self.tile_list[0]
        self.hero = Entity("images/hero.jpg", "hero", hero_stats)
        self.hero.color = arcade.color.BLUE_GRAY
        self.hero.position = start_tile.position
        self.entity_list.append(self.hero)

        for _ in range(3):
            enemy_stats = {'max_hp': 15, 'damage_deal': 5}
            enemy = Entity("images/hero.jpg", "enemy", enemy_stats)
            enemy.color = arcade.color.RED

            while True:
                r_x = random.randint(0, GRID_WIDTH - 1)
                r_y = random.randint(0, GRID_HEIGHT - 1)
                dist = math.sqrt(
                    (r_x - start_tile.properties['grid_x']) ** 2 + (r_y - start_tile.properties['grid_y']) ** 2)
                if 3 < dist <= 20:
                    enemy.center_x = r_x * TILE_SIZE + TILE_SIZE / 2
                    enemy.center_y = r_y * TILE_SIZE + TILE_SIZE / 2
                    self.entity_list.append(enemy)
                    self.enemy_list.append(enemy)
                    break

        self.camera.position = self.hero.position

    def on_update(self, delta_time):
        self.camera.position = arcade.math.lerp_2d(
            self.camera.position,
            self.hero.position,
            0.1
        )
        for entity in self.entity_list:
            current_hp = entity.get_stat('hp')
            if current_hp <= 0:
                entity.kill()
                print(f"{entity.role} повержен!")
            elif current_hp > entity['max_hp']:
                # Если HP выше максимума (лечение), ограничиваем
                entity['hp'] = entity['max_hp']

    def on_draw(self):
        self.clear()
        self.camera.use()
        self.tile_list.draw()
        self.entity_list.draw()

        for entity in self.entity_list:
            arcade.draw_text(f"HP: {entity.get_stat('hp')}",
                             entity.center_x, entity.center_y + 40,
                             arcade.color.WHITE, 12, anchor_x="center")

    def end_turn(self):
        print("Конец хода. Сброс эффектов.")
        for entity in self.entity_list:
            entity.reset_temp_stats()
        self.hero['moves_left'] = self.hero['move_range']

    def on_mouse_press(self, x, y, button, modifiers):
        print(self.hero.temp_stats['temporary_hp'])
        world_point = self.camera.unproject((x, y))
        world_x, world_y = world_point[0], world_point[1]

        clicked_entities = arcade.get_sprites_at_point((world_x, world_y), self.entity_list)

        if clicked_entities:
            target = clicked_entities[0]
            if target == self.hero:
                self.selected_unit = self.hero
                print("Выбран герой")
            elif self.selected_unit == self.hero and target.role == 'enemy':
                self.apply_ability(self.hero, target)
                self.hero['moves_left'] -= 1

        elif self.selected_unit == self.hero:
            clicked_tiles = arcade.get_sprites_at_point((world_x, world_y), self.tile_list)
            if clicked_tiles:
                tile = clicked_tiles[0]
                self.hero.position = tile.position
                self.hero['moves_left'] -= 1

        if self.hero['moves_left'] <= 0:
            print("Ход врагов!")
            for enemy in self.enemy_list:
                self.apply_ability(enemy, self.hero)
            self.end_turn()

    def apply_ability(self, source: Entity, target: Entity):
        # Пример: Наносим урон и вешаем бафф на себя (временное HP)
        effect_script = "target['hp'] -= 5; hero['temporary_hp'] += 4"

        # Получаем текущие суммарные значения
        s_data = source.get_as_dict() | source.temp_stats
        t_data = target.get_as_dict() | target.temp_stats

        context = {
            'hero': s_data,
            'target': t_data,
            'd4': random.randint(1, 4),
            'd20': random.randint(1, 20)
        }

        try:
            for cmd in effect_script.split(';'):
                if cmd.strip():
                    exec(cmd.strip(), {}, context)
        except Exception as e:
            print(f"Ошибка скрипта: {e}")

        # Обновляем основные статы и записываем разницу во временные
        # Обработка цели
        for key in list(target.stats_dict.keys()) + list(target.temp_stats.keys()):
            new_total = context['target'][key]
            if 'temp' in key:
                target.temp_stats[key] = context['target'][key]
            else:
                target.stats_dict[key] = new_total

        # Обработка источника
        for key in list(source.stats_dict.keys()) + list(source.temp_stats.keys()):
            new_total = context['hero'][key]
            if 'temp' in key:
                source.temp_stats[key] = context['hero'][key]
            else:
                source.stats_dict[key] = new_total


        return True


def main():
    window = MyGame()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()