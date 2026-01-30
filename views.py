import arcade
from arcade.gui import UIManager
from arcade.gui.widgets.layout import UIAnchorLayout
import random
import math
import time
from perlin_noise import PerlinNoise
from constants import *
from entities import Entity, Lair
from game_logic import bfs_path, apply_ability, load_characters_from_zip
from ui import CharacterInfoOverlay
import database


class ResourceManager:
    start_frames = []
    lose_frames = []
    loaded = False

    @classmethod
    def load_resources(cls):
        if cls.loaded:
            return
        try:
            for i in range(51):
                filename = f"images/start_menu/start_menu_{i:03d}.jpg"
                cls.start_frames.append(arcade.load_texture(filename))
        except:
            pass
        try:
            for i in range(51):
                filename = f"images/lose_menu/lose_menu_{i:03d}.jpg"
                cls.lose_frames.append(arcade.load_texture(filename))
        except:
            pass
        # Загрузка звуков (заглушки при ошибке)
        try:
            cls.start_music = arcade.load_sound('sound/Dota_2_-_Main_Menu_Flute_Theme_75018976.mp3')
            cls.lose_music = arcade.load_sound('sound/Giulio-Fazio-Wandering-Knight_lose_misic.mp3')
            cls.game_music = arcade.load_sound('sound/backgound_witcher.mp3')
            cls.bar_music = arcade.load_sound('sound/tavern_witcher.mp3')
        except:
            cls.start_music = arcade.load_sound(':resources:/music/1918.mp3')
            cls.lose_music = arcade.load_sound(':resources:/music/1918.mp3')
            cls.game_music = arcade.load_sound(':resources:/music/1918.mp3')
            cls.bar_music = arcade.load_sound(':resources:/music/funkyrobot.mp3')
        try:
            cls.button = arcade.load_texture('images/button.png')
            cls.hover_button = arcade.load_texture('images/hover_button.png')
        except:
            cls.button = arcade.load_texture(':resources:/gui_basic_assets/button/red_normal.png')
            cls.hover_button = arcade.load_texture(':resources:/gui_basic_assets/button/red_hover.png')
        cls.loaded = True


class LoadingView(arcade.View):
    def __init__(self):
        super().__init__()
        try:
            self.logo = arcade.load_texture("images/logo.png")
        except:
            self.logo = arcade.load_texture(':resources:/images/pinball/bumper.png')
        self.loaded_frame_count = 0

    def on_show_view(self):
        arcade.set_background_color(arcade.color.BLACK)
        database.init_db()  # Инициализация БД при запуске

    def on_draw(self):
        self.clear()
        if self.logo:
            arcade.draw_texture_rect(self.logo,
                                     arcade.rect.LBWH(SCREEN_WIDTH / 2 - 150, SCREEN_HEIGHT / 2 - 150, 300, 300))
        else:
            arcade.draw_text("LOADING...", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, arcade.color.WHITE, 30,
                             anchor_x="center")

    def on_update(self, delta_time):
        self.loaded_frame_count += 1
        if self.loaded_frame_count > 1:
            ResourceManager.load_resources()
            self.window.show_view(StartView())


class StartView(arcade.View):
    def __init__(self):
        super().__init__()
        self.view_camera = arcade.camera.Camera2D()
        self.current_frame = 0
        self.anim_timer = 0.0
        self.manager = UIManager()
        self.manager.enable()
        self.anchor_layout = UIAnchorLayout()
        self.manager.add(self.anchor_layout)
        self.setup_widgets()

    def on_click_continue(self, event):
        # Попытка загрузить игру
        data = database.load_game_state()
        if data:
            self.manager.disable()
            game_view = GameView()
            game_view.setup(load_data=data)
            arcade.stop_sound(self.start_player)
            self.window.show_view(game_view)
        else:
            print("Нет сохранений!")

    def on_click_new_game(self, event):
        self.manager.disable()
        game_view = GameView()
        game_view.setup(load_data=None)  # Новая игра
        if game_view.success:
            arcade.stop_sound(self.start_player)
            self.window.show_view(game_view)
        else:
            self.manager.enable()

    def on_click_quit(self, event):
        arcade.exit()

    def on_show_view(self):
        self.start_player = ResourceManager.start_music.play(loop=True)
        arcade.set_background_color(arcade.color.BLACK)

    def on_update(self, delta_time):
        if ResourceManager.start_frames:
            self.anim_timer += delta_time
            if self.anim_timer > 0.065:
                self.anim_timer = 0
                self.current_frame = (self.current_frame + 1) % len(ResourceManager.start_frames)

    def on_draw(self):
        self.clear()
        self.view_camera.use()
        if ResourceManager.start_frames:
            texture = ResourceManager.start_frames[self.current_frame]
            arcade.draw_texture_rect(texture, arcade.rect.LBWH(0, 0, self.width, self.height))
        else:
            arcade.draw_text("МЕНЮ", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, arcade.color.WHITE, 30, anchor_x="center")
        self.manager.draw()

    def setup_widgets(self):
        self.v_box = arcade.gui.UIBoxLayout()
        button_style = {
            "normal": {"font_name": ("Arial",), "font_size": 18, "font_color": arcade.color.LIME_GREEN},
            "hover": {"font_name": ("Arial",), "font_size": 18, "font_color": arcade.color.MALACHITE},
            "press": {"font_name": ("Arial",), "font_size": 18, "font_color": arcade.color.MALACHITE}
        }

        continue_btn = arcade.gui.UITextureButton(text="Продолжить", width=225, texture=ResourceManager.button,
                                                  texture_hovered=ResourceManager.hover_button, style=button_style)
        self.v_box.add(continue_btn)
        continue_btn.on_click = self.on_click_continue

        new_game_btn = arcade.gui.UITextureButton(text="Новая Игра", width=225, texture=ResourceManager.button,
                                                  texture_hovered=ResourceManager.hover_button, style=button_style)
        self.v_box.add(new_game_btn)
        new_game_btn.on_click = self.on_click_new_game

        quit_btn = arcade.gui.UITextureButton(text="Выход", width=225, texture=ResourceManager.button,
                                              texture_hovered=ResourceManager.hover_button, style=button_style)
        self.v_box.add(quit_btn)
        quit_btn.on_click = self.on_click_quit

        self.anchor_layout.add(anchor_x="left", anchor_y="center_y", align_x=55, align_y=-50, child=self.v_box)


class GameOverView(arcade.View):
    def __init__(self):
        super().__init__()
        self.view_camera = arcade.camera.Camera2D()
        self.current_frame = 0
        self.anim_timer = 0.0


    def on_show_view(self):
        self.lose_player = ResourceManager.lose_music.play(loop=True, speed=0.75)
        arcade.set_background_color(arcade.color.BLACK)

    def on_update(self, delta_time):
        if ResourceManager.lose_frames:
            self.anim_timer += delta_time
            if self.anim_timer > 0.05:
                self.anim_timer = 0
                self.current_frame = (self.current_frame + 1) % len(ResourceManager.lose_frames)

    def on_draw(self):
        self.clear()
        self.view_camera.use()
        if ResourceManager.lose_frames:
            texture = ResourceManager.lose_frames[self.current_frame]
            arcade.draw_texture_rect(texture, arcade.rect.LBWH(0, 0, self.width, self.height))
        else:
            arcade.draw_text("GAME OVER", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, arcade.color.RED, 50, anchor_x="center")

    def on_key_press(self, symbol, modifiers):
        arcade.stop_sound(self.lose_player)
        self.window.show_view(StartView())

class BarView(arcade.View):
    """ Локация Бара с физикой """

    def __init__(self, game_view):
        super().__init__()
        self.game_view = game_view

        self.scene = None
        self.player_sprite = None
        self.physics_engine = None
        self.camera = None
        self.scale = 3.2
        self.map_width = 15 * (30 * self.scale)
        self.map_height = 10 * (30 * self.scale)

        arcade.set_background_color(arcade.color.BLACK)

    def setup(self):
        self.camera = arcade.camera.Camera2D()
        # Загрузка карты
        layer_options = {
            "collisions": {
                "use_spatial_hash": True
            },
        }

        # Пытаемся загрузить карту
        try:
            self.tile_map = arcade.load_tilemap("maps/bar.tmx", scaling=self.scale, layer_options=layer_options)
            self.scene = arcade.Scene.from_tilemap(self.tile_map)
        except Exception as e:
            print(f"Ошибка загрузки карты бара: {e}.")
            self.window.show_view(self.game_view)

        # Игрок
        self.player_sprite = arcade.Sprite(self.game_view.selected_unit.texture)
        self.player_sprite.width, self.player_sprite.height = (70, 90)
        self.player_sprite.center_x = 200
        self.player_sprite.center_y = 200
        self.scene.add_sprite("Player", self.player_sprite)

        # Физика
        self.physics_engine = arcade.PhysicsEngineSimple(
            self.player_sprite,
            walls=self.scene["collisions"] if "collisions" in self.scene._name_mapping else arcade.SpriteList()
        )

    def on_show_view(self):
        self.bar_player = ResourceManager.bar_music.play(volume=0.55,loop=True)

    def on_draw(self):
        self.clear()
        self.camera.use()
        self.scene.draw()


    def on_update(self, delta_time):
        self.physics_engine.update()
        self.player_sprite.center_x = max(self.player_sprite.width // 2, min(self.player_sprite.center_x,
                                                                             self.map_width - self.player_sprite.width // 2))
        self.player_sprite.center_y = max(self.player_sprite.height // 2, min(self.player_sprite.center_y,
                                                                              self.map_height - self.player_sprite.height // 2))

        # Слежение камеры с ограничением
        new_camera_x = max(self.camera.viewport_width // 2,
                           min(self.player_sprite.center_x, self.map_width - self.camera.viewport_width // 2))
        new_camera_y = max(self.camera.viewport_height // 2,
                           min(self.player_sprite.center_y, self.map_height - self.camera.viewport_height // 2))

        self.camera.position = (new_camera_x, new_camera_y)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.W:
            self.player_sprite.change_y = PLAYER_BAR_SPEED
        elif key == arcade.key.S:
            self.player_sprite.change_y = -PLAYER_BAR_SPEED
        elif key == arcade.key.A:
            self.player_sprite.change_x = -PLAYER_BAR_SPEED
        elif key == arcade.key.D:
            self.player_sprite.change_x = PLAYER_BAR_SPEED
        elif key == arcade.key.ESCAPE:
            # Выход из бара
            arcade.stop_sound(self.bar_player)
            self.window.show_view(self.game_view)

    def on_key_release(self, key, modifiers):
        if key in [arcade.key.W, arcade.key.S]:
            self.player_sprite.change_y = 0
        elif key in [arcade.key.A, arcade.key.D]:
            self.player_sprite.change_x = 0


class GameView(arcade.View):
    def __init__(self):
        super().__init__()
        self.map_seed = None  # Для сохранения
        self.tile_list = None
        self.entity_list = None
        self.fog_list = None
        self.enemy_list = None
        self.heroes_list = None
        self.lairs_list = []
        self.camera = None
        self.camera_vel = [0, 0]
        self.camera_mode = "FOLLOW"
        self.current_unit_index = 0
        self.selected_unit = None
        self.turn_state = PLAYER_TURN
        self.pending_buffs = []
        arcade.set_background_color(arcade.color.BLACK)

    def on_show_view(self):
        self.background_music_player = ResourceManager.game_music.play(volume=0.4, loop=True)

    def setup(self, load_data=None):
        self.tile_list = arcade.SpriteList()
        self.entity_list = arcade.SpriteList()
        self.enemy_list = arcade.SpriteList()
        self.heroes_list = arcade.SpriteList()
        self.fog_list = arcade.SpriteList()
        self.ui_camera = arcade.camera.Camera2D()
        self.char_info_overlay = CharacterInfoOverlay()
        self.lairs_list = []
        self.camera = arcade.camera.Camera2D()

        # 1. Генерация карты (из сохранения или новая)
        if load_data:
            self.map_seed = load_data['seed']
            random.seed(self.map_seed)  # Восстанавливаем рандом для карты
        else:
            self.map_seed = random.randint(1, 100000)
            random.seed(self.map_seed)

        noise = PerlinNoise(octaves=4, seed=self.map_seed)

        self.grid_types = [['meadow' for _ in range(GRID_HEIGHT)] for _ in range(GRID_WIDTH)]
        tavern_locations = []
        valid_spawn_tiles = []
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                n = noise([x / GRID_WIDTH, y / GRID_HEIGHT])
                tile_type = "meadow"
                if n < -0.10:
                    tile_type = "forest"
                elif n > 0.275:
                    tile_type = "town"
                self.grid_types[x][y] = tile_type

        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                tile_type = self.grid_types[x][y]
                if tile_type == "town":
                    valid = True
                    for dx in range(-1, 2):
                        for dy in range(-1, 2):
                            nx, ny = x + dx, y + dy
                            if not (1 < nx < GRID_WIDTH and 1 < ny < GRID_HEIGHT) or self.grid_types[nx][ny] != 'town':
                                valid = False
                    if valid:
                        too_close = any(math.sqrt((x - tx) ** 2 + (y - ty) ** 2) < 17 for tx, ty in tavern_locations)
                        if not too_close:
                            tile_type = "bar"
                            tavern_locations.append((x, y))

                img_file = "images/meadow2.jpg"
                if tile_type == "forest":
                    img_file = "images/forest2.jpg"
                elif tile_type == "town":
                    img_file = "images/town_dark.jpg"
                elif tile_type == "bar":
                    img_file = "images/bar2.jpg"

                try:
                    tile = arcade.Sprite(img_file)
                except:
                    color = arcade.color.GREEN
                    if tile_type == 'town':
                        color = arcade.color.DARK_SLATE_GRAY
                    elif tile_type == 'bar':
                        color = arcade.color.GOLD
                    elif tile_type == 'forest':
                        color = arcade.color.FOREST_GREEN
                    tile = arcade.SpriteSolidColor(TILE_SIZE, TILE_SIZE, color)

                tile.width = TILE_SIZE
                tile.height = TILE_SIZE
                tile.center_x = x * TILE_SIZE + TILE_SIZE / 2
                tile.center_y = y * TILE_SIZE + TILE_SIZE / 2
                tile.properties = {'type': tile_type, 'grid_x': x, 'grid_y': y}
                self.tile_list.append(tile)
                if tile_type == "bar": valid_spawn_tiles.append(tile)

                try:
                    fog = arcade.Sprite("images/_fog.png")
                except:
                    fog = arcade.SpriteSolidColor(TILE_SIZE, TILE_SIZE, arcade.color.GRAY)
                fog.center_x = tile.center_x
                fog.center_y = tile.center_y
                fog.width = TILE_SIZE
                fog.height = TILE_SIZE
                fog.alpha = 255
                self.fog_list.append(fog)

        # 2. Загрузка сущностей
        if load_data:
            # Восстанавливаем сущности из БД
            for ent_data in load_data['entities']:
                if ent_data['role'] == 'hero':
                    hero = Entity(ent_data['image_path'], "hero", stats_dict=ent_data['stats'])
                    hero.active_effects = ent_data['effects']
                    hero.abilities = ent_data['abilities']
                    hero.center_x, hero.center_y = ent_data['x'], ent_data['y']
                    self.entity_list.append(hero)
                    self.heroes_list.append(hero)
                else:
                    is_guardian = ent_data['is_guardian']
                    enemy = Entity(ent_data['image_path'], "enemy", stats_dict=ent_data['stats'])
                    enemy.active_effects = ent_data['effects']
                    enemy.abilities = ent_data['abilities']
                    enemy.is_guardian = is_guardian
                    enemy.center_x, enemy.center_y = ent_data['x'], ent_data['y']
                    self.entity_list.append(enemy)
                    self.enemy_list.append(enemy)

            # Восстанавливаем логова
            for l_data in load_data['lairs']:
                lair = Lair((l_data['x'], l_data['y']))
                lair.center_x, lair.center_y = l_data['x'], l_data['y']
                lair.guardians_needed = l_data['guardians_needed']
                lair.next_spawn_interval = l_data['next_spawn_interval']
                lair.guardians_spawned = l_data['guardians_spawned']
                self.lairs_list.append(lair)
                self.tile_list.append(lair)

        else:
            # Новая игра
            if not valid_spawn_tiles: valid_spawn_tiles.append(self.tile_list[0])
            spawn_point = random.choice(valid_spawn_tiles)
            heroes = load_characters_from_zip()
            if not heroes:
                self.success = False
                return
            self.success = True
            positions = [
                (spawn_point.position[0] - TILE_SIZE, spawn_point.position[1] - TILE_SIZE),
                (spawn_point.position[0] + TILE_SIZE, spawn_point.position[1] - TILE_SIZE),
                (spawn_point.position[0] - TILE_SIZE, spawn_point.position[1] + TILE_SIZE),
                (spawn_point.position[0] + TILE_SIZE, spawn_point.position[1] + TILE_SIZE)
            ]

            # Создаем героев
            for i in range(len(heroes)):
                hero = Entity(f"images/hero_{i + 1}.jpg", "hero", json_data=heroes[i])
                hero.position = positions[i]
                self.entity_list.append(hero)
                self.heroes_list.append(hero)

            # создаем логова
            spawn_gx = spawn_point.properties['grid_x']
            spawn_gy = spawn_point.properties['grid_y']
            created_lairs = 0
            attempts = 0
            while created_lairs < 3 and attempts < 1000:
                attempts += 1
                lx = random.randint(2, GRID_WIDTH - 3)
                ly = random.randint(2, GRID_HEIGHT - 3)
                if math.sqrt((lx - spawn_gx) ** 2 + (ly - spawn_gy) ** 2) < 15:
                    continue

                too_close = False
                for l in self.lairs_list:
                    if math.sqrt((lx - l.center_x / TILE_SIZE) ** 2 + (ly - l.center_y / TILE_SIZE) ** 2) < 10:
                        too_close = True
                        break
                if not too_close:
                    l_pos = (lx * TILE_SIZE + TILE_SIZE / 2, ly * TILE_SIZE + TILE_SIZE / 2)
                    lair = Lair(l_pos)
                    self.lairs_list.append(lair)
                    self.tile_list.append(lair)
                    created_lairs += 1

        self.selected_unit = self.heroes_list[0]
        self.camera.position = self.selected_unit.position


    def enemy_turn_logic(self):
        print("Враги думают...")

        # 1. Собираем препятствия (Города, Бары, Другие враги, Герои)
        obstacles = set()

        # города
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                if self.grid_types[x][y] in ['town', 'bar']:
                    obstacles.add((x, y))

        # герои
        for h in self.heroes_list:
            obstacles.add((int(h.center_x // TILE_SIZE), int(h.center_y // TILE_SIZE)))

        # враги
        enemy_positions = {}  # Map index -> pos
        for idx, enemy in enumerate(self.enemy_list):
            pos = (int(enemy.center_x // TILE_SIZE), int(enemy.center_y // TILE_SIZE))
            enemy_positions[idx] = pos
            obstacles.add(pos)

        # 2. Планируем путь для каждого врага
        for idx, enemy in enumerate(self.enemy_list):
            # Временно убираем текущую позицию этого врага из препятствий, чтобы он мог выйти
            current_pos = enemy_positions[idx]
            if current_pos in obstacles:
                obstacles.remove(current_pos)

            closest_hero = None
            min_dist = float('inf')
            e_gx, e_gy = current_pos

            # Ищем цель
            for hero in self.heroes_list:
                h_gx = int(hero.center_x // TILE_SIZE)
                h_gy = int(hero.center_y // TILE_SIZE)
                dist = abs(e_gx - h_gx) + abs(e_gy - h_gy)
                if dist < min_dist:
                    min_dist = dist
                    closest_hero = hero

            if closest_hero:
                # для поиска пути временно убираем героя из obstacles
                hero_pos = (int(closest_hero.center_x // TILE_SIZE), int(closest_hero.center_y // TILE_SIZE))
                if hero_pos in obstacles:
                    obstacles.remove(hero_pos)

                path = bfs_path((e_gx, e_gy), hero_pos, obstacles=obstacles)

                # Возвращаем героя в obstacles
                obstacles.add(hero_pos)

                if len(path) > 0:
                    # Если путь найден
                    move_limit = enemy.get_stat('move_range')[0]
                    real_steps = path
                    if real_steps and real_steps[-1] == hero_pos:
                        real_steps.pop()  # Убираем клетку героя из маршрута перемещения

                    # Ограничиваем дальность
                    steps = real_steps[:move_limit]

                    if len(path) <= enemy.get_stat('attack_range')[0]:
                        enemy.selected_ability = random.choice(enemy.abilities)
                        print(f'Противник использует способность:\n{enemy.selected_ability.get('name', '')}')
                        apply_ability(enemy, closest_hero,
                                      enemy.selected_ability.get('effect', 'The entity does not have any abilities'))
                        # остаемся на месте и возвращаем в obstacles
                        obstacles.add(current_pos)
                    else:
                        # двигаемся
                        for sx, sy in steps:
                            world_x = sx * TILE_SIZE + TILE_SIZE / 2
                            world_y = sy * TILE_SIZE + TILE_SIZE / 2
                            enemy.path_queue.append((world_x, world_y))

                        # новая позиция врага
                        obstacles.add(steps[-1])
                else:
                    # пути нет (заблокирован) - стоим
                    obstacles.add(current_pos)
            else:
                # нет героев - стоим
                obstacles.add(current_pos)

        self.turn_state = ENEMY_MOVING

    def on_key_press(self, key, modifiers):
        # Сохранение по F5
        if key == arcade.key.F5:
            database.save_game_state(self.map_seed, self.heroes_list, self.enemy_list, self.lairs_list)
            return

        if self.turn_state != PLAYER_TURN:
            return
        if key == arcade.key.UP:
            self.camera_vel[1] = 1
        elif key == arcade.key.DOWN:
            self.camera_vel[1] = -1
        elif key == arcade.key.LEFT:
            self.camera_vel[0] = -1
        elif key == arcade.key.RIGHT:
            self.camera_vel[0] = 1
        elif key == arcade.key.TAB:
            if self.heroes_list:
                self.current_unit_index = (self.current_unit_index + 1) % len(self.heroes_list)
                self.selected_unit = self.heroes_list[self.current_unit_index]
                self.camera_mode = "FOLLOW"
        elif key == arcade.key.ENTER:
            if self.selected_unit:
                tiles = arcade.get_sprites_at_point(self.selected_unit.position, self.tile_list)
                if tiles and tiles[0].properties.get('type') == 'bar':
                    bar_view = BarView(self)
                    arcade.stop_sound(self.background_music_player)
                    bar_view.setup()
                    self.window.show_view(bar_view)

    def on_key_release(self, key, modifiers):
        if key in [arcade.key.UP, arcade.key.DOWN]:
            self.camera_vel[1] = 0
        if key in [arcade.key.LEFT, arcade.key.RIGHT]:
            self.camera_vel[0] = 0

    def on_update(self, delta_time):
        if len(self.lairs_list) == 0:
            print("ПОБЕДА!")
            self.window.show_view(StartView())
            return
        elif len(self.heroes_list) == 0:
            arcade.stop_sound(self.background_music_player)
            self.window.show_view(GameOverView())
            return
        if self.char_info_overlay.visible:
            self.char_info_overlay.update(delta_time)

        if self.turn_state == ENEMY_CALCULATING:
            self.enemy_turn_logic()
        elif self.turn_state == ENEMY_MOVING:
            any_moving = False
            for enemy in self.enemy_list:
                enemy.update_position()
                if enemy.is_moving: any_moving = True
            if not any_moving:
                self.turn_state = PLAYER_TURN
                for unit in self.heroes_list:
                    unit['moves_left'] = unit['moves_count']
                print("Ход игрока!")

        for hero in self.heroes_list:
            hero.update_position()

        # Камера
        map_w = GRID_WIDTH * TILE_SIZE
        map_h = GRID_HEIGHT * TILE_SIZE
        half_view_w = (SCREEN_WIDTH / 2)
        half_view_h = (SCREEN_HEIGHT / 2)
        nx, ny = self.camera.position
        if self.camera_vel[0] != 0 or self.camera_vel[1] != 0:
            self.camera_mode = "FREE"
            nx += self.camera_vel[0] * CAMERA_SPEED
            ny += self.camera_vel[1] * CAMERA_SPEED
        elif self.camera_mode == "FOLLOW" and self.selected_unit:
            nx, ny = arcade.math.lerp_2d(self.camera.position, self.selected_unit.position, 0.1)
        self.camera.position = (
        max(half_view_w, min(nx, map_w - half_view_w)), max(half_view_h, min(ny, map_h - half_view_h)))

        # Туман
        if self.heroes_list:
            if self.turn_state == PLAYER_TURN:
                self.current_unit_index = self.current_unit_index % len(self.heroes_list)
                active_unit = self.heroes_list[self.current_unit_index]
                self.selected_unit = active_unit
            for hero in self.heroes_list:
                view_dist = hero.get_stat('view_range')[0] * TILE_SIZE
                for fog in self.fog_list:
                    if not fog.visible:
                        continue
                    d = math.sqrt((fog.center_x - hero.center_x) ** 2 + (fog.center_y - hero.center_y) ** 2)
                    if d <= view_dist:
                        fog.alpha = max(0, fog.alpha - 15)
                        if fog.alpha == 0: fog.visible = False

        # Логова
        for lair in self.lairs_list:
            min_dist = float('inf')
            for hero in self.heroes_list:
                d = math.sqrt((hero.center_x - lair.center_x) ** 2 + (hero.center_y - lair.center_y) ** 2)
                if d < min_dist: min_dist = d
            if (min_dist / TILE_SIZE) < 5 and not lair.guardians_spawned:
                lair.guardians_spawned = True
                lx, ly = int(lair.center_x // TILE_SIZE), int(lair.center_y // TILE_SIZE)
                c = 0
                for dx in range(-2, 3):
                    for dy in range(-2, 3):
                        if c >= 6:
                            break
                        if (dx == 0 and dy == 0 or
                                arcade.get_sprites_at_point((lx * TILE_SIZE, ly * TILE_SIZE), self.entity_list)):
                            continue
                        self.spawn_enemy(lx + dx, ly + dy, is_guardian=True)
                        c += 1
            if time.time() - lair.last_spawn_time > lair.next_spawn_interval:
                lair.last_spawn_time = time.time()
                lair.next_spawn_interval = random.randint(40, 90)
                lx, ly = int(lair.center_x // TILE_SIZE), int(lair.center_y // TILE_SIZE)
                for _ in range(3):
                    for sx in range(-2, 2):
                        for sy in range(-2, 2):
                            if (not (arcade.get_sprites_at_point((lx * TILE_SIZE, ly * TILE_SIZE), self.entity_list))
                                    and sx != 0 and sy != 0):
                                self.spawn_enemy(lx + sx, ly + ly)
            if lair.guardians_needed <= 0:
                lair.kill()
                self.lairs_list.remove(lair)

        # Смерть
        for entity in self.entity_list:
            if entity.get_stat('hp')[0] <= 0:
                if getattr(entity, 'is_guardian', False):
                    n_lair, min_d = None, float('inf')
                    for l in self.lairs_list:
                        d = math.sqrt((entity.center_x - l.center_x) ** 2 + (entity.center_y - l.center_y) ** 2)
                        if d < min_d: min_d = d; n_lair = l
                    if n_lair and min_d < TILE_SIZE * 10: n_lair.guardians_needed -= 1
                entity.kill()
                if entity in self.heroes_list: self.heroes_list.remove(entity)
                if entity in self.enemy_list: self.enemy_list.remove(entity)
            elif entity.get_stat('hp')[-1] > entity.get_stat('max_hp')[0]:
                entity['hp'] = entity.get_stat('max_hp')[0] + entity.get_stat('hp')[1]

    def on_draw(self):
        self.clear()
        if self.camera: self.camera.use()
        self.tile_list.draw()
        self.entity_list.draw()
        for lair in self.lairs_list:
            arcade.draw_text(f"{lair.guardians_needed}", lair.center_x, lair.center_y + 50, arcade.color.RED, 14,
                             anchor_x="center")
        self.fog_list.draw()
        self.ui_camera.use()
        self.char_info_overlay.draw()

    def spawn_enemy(self, x_grid, y_grid, is_guardian=False):
        if is_guardian:
            enemy = Entity('images/guardian.jpg', 'enemy', json_data=GUARD_JSON.copy())
        else:
            enemy = Entity("images/enemy.jpg", "enemy", json_data=ENEMY_JSON.copy())
        enemy.is_guardian = is_guardian
        enemy.center_x = x_grid * TILE_SIZE + TILE_SIZE / 2
        enemy.center_y = y_grid * TILE_SIZE + TILE_SIZE / 2
        self.entity_list.append(enemy)
        self.enemy_list.append(enemy)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        self.char_info_overlay.on_scroll(scroll_y)

    def end_turn(self):
        print("Конец хода игрока.")
        for entity in self.entity_list:
            entity.update_effects_turn()
        self.turn_state = ENEMY_CALCULATING

    def on_mouse_press(self, x, y, button, modifiers):
        if self.turn_state != PLAYER_TURN:
            return
        world_point = self.camera.unproject((x, y))
        wx, wy = world_point[0], world_point[1]

        # Инфо по ПКМ
        if button == arcade.MOUSE_BUTTON_RIGHT:
            clicked = arcade.get_sprites_at_point(world_point, self.entity_list)
            if clicked:
                target = clicked[0]
                new_pos = "left"
                if self.char_info_overlay.visible and self.char_info_overlay.position == "left": new_pos = "right"
                self.char_info_overlay.show(target, position=new_pos)
            else:
                self.char_info_overlay.hide()
            return

        # ЛКМ действия
        active_hero = self.heroes_list[self.current_unit_index] if self.heroes_list else None
        if not active_hero or active_hero.path_queue:
            return
        clicked = arcade.get_sprites_at_point((wx, wy), self.entity_list)

        if clicked:
            target = clicked[0]
            if target in self.heroes_list:
                if not self.selected_unit.selected_ability:
                    self.selected_unit = target
                    self.current_unit_index = self.heroes_list.index(target)
                else:
                    apply_ability(self.selected_unit, target, self.selected_unit.selected_ability)
                    self.selected_unit.selected_ability = None
            elif target.role == 'enemy':
                dist = abs(active_hero.center_x - target.center_x) + abs(active_hero.center_y - target.center_y)
                if dist // TILE_SIZE < active_hero['move_range'] and active_hero['moves_left'] > 0:
                    if active_hero.selected_ability:
                        apply_ability(active_hero, target, active_hero.selected_ability)
                        active_hero['moves_left'] -= 1
                    else:
                        print('Способность не выбрана')
        else:
            clicked_tiles = arcade.get_sprites_at_point((wx, wy), self.tile_list)
            if clicked_tiles:
                tile = clicked_tiles[0]
                start_gx = int(active_hero.center_x // TILE_SIZE)
                start_gy = int(active_hero.center_y // TILE_SIZE)
                end_gx = int(tile.center_x // TILE_SIZE)
                end_gy = int(tile.center_y // TILE_SIZE)
                dist = abs(end_gx - start_gx) + abs(end_gy - start_gy)

                if active_hero.get_stat('moves_left')[0] > 0 and dist <= active_hero.get_stat('move_range')[0]:
                    path = bfs_path((start_gx, start_gy), (end_gx, end_gy))
                    for sx, sy in path:
                        world_x = sx * TILE_SIZE + TILE_SIZE / 2
                        world_y = sy * TILE_SIZE + TILE_SIZE / 2
                        active_hero.path_queue.append((world_x, world_y))
                    active_hero['moves_left'] -= 1

        if all(u.get_stat('moves_left')[0] <= 0 for u in self.heroes_list):
            self.end_turn()



