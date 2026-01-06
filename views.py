import arcade
from arcade.gui import UIManager
from arcade.gui.widgets.layout import UIAnchorLayout
import random
import math
import time
from perlin_noise import PerlinNoise
from constants import *
from entities import Entity, Lair
from game_logic import bfs_path, apply_ability
from ui import CharacterInfoOverlay


class ResourceManager:
    """ Класс для предварительной загрузки ресурсов """
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
            print('Произошла ошибка при загрузке фона')
        try:
            for i in range(51):
                filename = f"images/lose_menu/lose_menu_{i:03d}.jpg"
                cls.lose_frames.append(arcade.load_texture(filename))
        except:
            print('Произошла ошибка при загрузке фона')
        try:
            cls.start_music = arcade.load_sound('sound/Dota_2_-_Main_Menu_Flute_Theme_75018976.mp3')
            cls.lose_music = arcade.load_sound('sound/Giulio-Fazio-Wandering-Knight_lose_misic.mp3')
            cls.game_music = arcade.load_sound('sound/backgound_witcher.mp3')
            cls.bar_music = arcade.load_sound('sound/tavern_witcher.mp3')
        except:
            print('Произошла ошибка при загрузке звуков')
            cls.start_music = arcade.load_sound(':resources:/music/1918.mp3')
            cls.lose_music = arcade.load_sound(':resources:/music/1918.mp3')
            cls.game_music = arcade.load_sound(':resources:/music/1918.mp3')
            cls.bar_music = arcade.load_sound(':resources:/music/funkyrobot.mp3')
        try:
            cls.button = arcade.load_texture('images/button.png')
            cls.hover_button = arcade.load_texture('images/hover_button.png')
        except:
            print('Произошла ошибка при загрузке текстур')
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

    def on_click_new_game(self, event):
        self.manager.disable()
        game_view = GameView()
        game_view.setup()
        arcade.stop_sound(self.start_player)
        self.window.show_view(game_view)

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
            arcade.draw_text("МЕНЮ: Нажмите любую клавишу", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, arcade.color.WHITE, 30,
                             anchor_x="center")
        self.manager.draw()

    def setup_widgets(self):
        # VBox для кнопок
        self.v_box = arcade.gui.UIBoxLayout()

        # Стиль кнопок
        style = {
            "normal": {
                "font_name": ("Arial",),
                "font_size": 20,
                "font_color": arcade.color.BRONZE,
            },
            "hover": {
                "font_name": ("Arial",),
                "font_size": 20,
                "font_color": arcade.color.BUFF,
                "border_width": 2,
                "border_color": arcade.color.GRAY,
                "bg_color": arcade.color.DARK_GRAY,
            },
            "press": {
                "font_name": ("Arial",),
                "font_size": 20,
                "font_color": arcade.color.BUFF,
                "border_width": 2,
                "border_color": arcade.color.GRAY,
                "bg_color": arcade.color.BLACK,
            }
        }
        button_style = {
            "normal": {
                "font_name": ("Times New Roman", "Arial"),
                "font_size": 18,
                "font_color": arcade.color.LIME_GREEN,
            },
            "hover": {
                "font_name": ("Times New Roman", "Arial"),
                "font_size": 18,
                "font_color": arcade.color.MALACHITE,
            },
            "press": {
                "font_name": ("Times New Roman", "Arial"),
                "font_size": 18,
                "font_color": arcade.color.MALACHITE,
            }
        }
        # Кнопка "Продолжить" (пока = Новая игра)
        continue_btn = arcade.gui.UITextureButton(text="Продолжить", width=225,
                                                  texture=ResourceManager.button,
                                                  texture_hovered=ResourceManager.hover_button,
                                                  style=button_style)
        self.v_box.add(continue_btn)
        continue_btn.on_click = self.on_click_new_game

        # Кнопка "Новая игра"
        new_game_btn = arcade.gui.UITextureButton(text="Новая Игра", width=225,
                                                  texture=ResourceManager.button,
                                                  texture_hovered=ResourceManager.hover_button,
                                                  texture_pressed=ResourceManager.hover_button,
                                                  style=button_style)
        self.v_box.add(new_game_btn)
        new_game_btn.on_click = self.on_click_new_game

        # Кнопка "Выход"
        quit_btn = arcade.gui.UITextureButton(text="Выход", width=225,
                                                  texture=ResourceManager.button,
                                                  texture_hovered=ResourceManager.hover_button,
                                                  texture_pressed=ResourceManager.hover_button,
                                                  style=button_style)
        self.v_box.add(quit_btn)
        quit_btn.on_click = self.on_click_quit
        self.anchor_layout.add(
            anchor_x="left",
            anchor_y="center_y",
            align_x=55,
            align_y=-50,
            child=self.v_box
        )


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
        self.tile_list = None
        self.entity_list = None
        self.fog_list = None
        self.enemy_list = None
        self.heroes_list = None
        self.lairs_list = []  # Список всех логов

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

    def setup(self):
        self.tile_list = arcade.SpriteList()
        self.entity_list = arcade.SpriteList()
        self.enemy_list = arcade.SpriteList()
        self.heroes_list = arcade.SpriteList()
        self.fog_list = arcade.SpriteList()
        self.ui_camera = arcade.camera.Camera2D()
        self.char_info_overlay = CharacterInfoOverlay()
        self.lairs_list = []

        self.camera = arcade.camera.Camera2D()
        noise = PerlinNoise(octaves=4)

        self.grid_types = [['meadow' for _ in range(GRID_HEIGHT)] for _ in range(GRID_WIDTH)]
        tavern_locations = []
        valid_spawn_tiles = []

        # Генерация карты
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                n = noise([x / GRID_WIDTH, y / GRID_HEIGHT])
                tile_type = "meadow"
                if n < -0.10:
                    tile_type = "forest"
                elif n > 0.275:
                    tile_type = "town"
                self.grid_types[x][y] = tile_type

        # Размещение объектов
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
                            print(tavern_locations)
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

                if tile_type == "bar":
                    valid_spawn_tiles.append(tile)

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

        # Герои
        if not valid_spawn_tiles:
            valid_spawn_tiles.append(self.tile_list[len(self.tile_list) // 2])
        spawn_point = random.choice(valid_spawn_tiles)
        positions = [
            (spawn_point.position[0] - TILE_SIZE, spawn_point.position[1] - TILE_SIZE),
            (spawn_point.position[0] + TILE_SIZE, spawn_point.position[1] - TILE_SIZE),
            (spawn_point.position[0] - TILE_SIZE, spawn_point.position[1] + TILE_SIZE),
            (spawn_point.position[0] + TILE_SIZE, spawn_point.position[1] + TILE_SIZE)
        ]

        hero_stats = [{'max_hp': 20, 'moves_count': 4},
                      {'max_hp': 35, 'moves_count': 3},
                      {'max_hp': 15, 'moves_count': 5}]
        for i in range(3):
            hero = Entity(f"images/hero_{i + 1}.jpg", "hero", json_data=SAMPLE_HERO_JSON.copy())
            hero.position = positions[i]
            self.entity_list.append(hero)
            self.heroes_list.append(hero)

        self.selected_unit = self.heroes_list[0]
        self.camera.position = self.selected_unit.position

        # Генерация 3 логов
        spawn_gx = spawn_point.properties['grid_x']
        spawn_gy = spawn_point.properties['grid_y']

        created_lairs = 0
        attempts = 0

        while created_lairs < 3 and attempts < 1000:
            attempts += 1
            lx = random.randint(2, GRID_WIDTH - 3)
            ly = random.randint(2, GRID_HEIGHT - 3)

            # 1. Далеко от спавна
            if math.sqrt((lx - spawn_gx) ** 2 + (ly - spawn_gy) ** 2) < 15: continue

            # 2. Далеко от других логов
            too_close_lair = False
            for existing_lair in self.lairs_list:
                ex = existing_lair.center_x // TILE_SIZE
                ey = existing_lair.center_y // TILE_SIZE
                if math.sqrt((lx - ex) ** 2 + (ly - ey) ** 2) < 10:
                    too_close_lair = True
                    break

            if not too_close_lair:
                l_pos = (lx * TILE_SIZE + TILE_SIZE / 2, ly * TILE_SIZE + TILE_SIZE / 2)
                lair = Lair(l_pos)
                self.lairs_list.append(lair)
                self.tile_list.append(lair)
                created_lairs += 1
                print(f"Логово {created_lairs} создано.")

    def spawn_enemy(self, x_grid, y_grid, is_guardian=False):
        if is_guardian:
            enemy = Entity('images/guardian.jpg', 'enemy', json_data=SAMPLE_HERO_JSON.copy())
        else:
            enemy = Entity("images/enemy.jpg", "enemy", json_data=SAMPLE_ENEMY_JSON.copy())
        enemy.is_guardian = is_guardian
        enemy.center_x = x_grid * TILE_SIZE + TILE_SIZE / 2
        enemy.center_y = y_grid * TILE_SIZE + TILE_SIZE / 2
        self.entity_list.append(enemy)
        self.enemy_list.append(enemy)

    def on_update(self, delta_time):
        # 0. Условие ПОБЕДЫ (Все логова уничтожены)
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
        # 1. Логика Ходов и Движения Врагов
        if self.turn_state == ENEMY_CALCULATING:
            self.enemy_turn_logic()

        elif self.turn_state == ENEMY_MOVING:
            any_moving = False
            for enemy in self.enemy_list:
                enemy.update_position()
                if enemy.is_moving:
                    any_moving = True

            if not any_moving:
                # Все враги дошли
                self.turn_state = PLAYER_TURN
                # Возвращаем ОД игрокам
                for unit in self.heroes_list:
                    unit['moves_left'] = unit['moves_count']
                print("Ход игрока!")

        # 2. Обновление анимации движения героев
        for hero in self.heroes_list:
            hero.update_position()

        # 3. Логика Камеры (Строгие границы)
        map_w = GRID_WIDTH * TILE_SIZE
        map_h = GRID_HEIGHT * TILE_SIZE

        half_view_w = (SCREEN_WIDTH / 2)
        half_view_h = (SCREEN_HEIGHT / 2)

        # Вычисляем желаемую позицию
        new_cam_x, new_cam_y = self.camera.position

        if self.camera_vel[0] != 0 or self.camera_vel[1] != 0:
            self.camera_mode = "FREE"
            new_cam_x += self.camera_vel[0] * CAMERA_SPEED
            new_cam_y += self.camera_vel[1] * CAMERA_SPEED
        elif self.camera_mode == "FOLLOW" and self.selected_unit:
            new_cam_x, new_cam_y = arcade.math.lerp_2d(self.camera.position, self.selected_unit.position, 0.1)

        # Центр камеры не может быть ближе к краю, чем половина экрана
        new_cam_x = max(half_view_w, min(new_cam_x, map_w - half_view_w))
        new_cam_y = max(half_view_h, min(new_cam_y, map_h - half_view_h))

        self.camera.position = (new_cam_x, new_cam_y)

        # 4. Туман
        if self.heroes_list:
            if self.turn_state == PLAYER_TURN:
                self.current_unit_index = self.current_unit_index % len(self.heroes_list)
                active_unit = self.heroes_list[self.current_unit_index]
                self.selected_unit = active_unit
            else:
                # Во время хода врага показываем то, где камера
                pass

            # Рассеиваем туман вокруг всех героев
            for hero in self.heroes_list:
                view_dist = hero.get_stat('view_range')[0] * TILE_SIZE
                for fog in self.fog_list:
                    if not fog.visible:
                        continue
                    d = math.sqrt((fog.center_x - hero.center_x) ** 2 + (fog.center_y - hero.center_y) ** 2)
                    if d <= view_dist:
                        fog.alpha = max(0, fog.alpha - 15)
                        if fog.alpha == 0:
                            fog.visible = False

        # 5. Логика Логов
        for lair in self.lairs_list:
            # Дистанция до ближайшего героя
            min_dist = float('inf')
            for hero in self.heroes_list:
                d = math.sqrt((hero.center_x - lair.center_x) ** 2 + (hero.center_y - lair.center_y) ** 2)
                if d < min_dist:
                    min_dist = d

            # Спавн стражей
            if (min_dist / TILE_SIZE) < 5 and not lair.guardians_spawned:
                lair.guardians_spawned = True
                print("Стражи призваны!")
                lx, ly = int(lair.center_x // TILE_SIZE), int(lair.center_y // TILE_SIZE)
                count = 0
                for dx in range(-2, 3):
                    for dy in range(-2, 3):
                        if count >= 6: break
                        if dx == 0 and dy == 0: continue
                        self.spawn_enemy(lx + dx, ly + dy, is_guardian=True)
                        count += 1

            # Бродячие монстры
            if time.time() - lair.last_spawn_time > lair.next_spawn_interval:
                lair.last_spawn_time = time.time()
                lair.next_spawn_interval = random.randint(40, 90)
                lx, ly = int(lair.center_x // TILE_SIZE), int(lair.center_y // TILE_SIZE)
                for _ in range(3):
                    self.spawn_enemy(lx + random.randint(-2, 2), ly + random.randint(-2, 2))

            # Уничтожение логова
            if lair.guardians_needed <= 0:
                print("Одно из логов уничтожено!")
                lair.kill()
                self.lairs_list.remove(lair)

        # 6. Смерть
        for entity in self.entity_list:
            if entity.get_stat('hp')[0] <= 0:
                if getattr(entity, 'is_guardian', False):
                    # Ищем к какому логову относился этот страж (по расстоянию)
                    nearest_lair = None
                    min_l_dist = float('inf')
                    for l in self.lairs_list:
                        dist = math.sqrt((entity.center_x - l.center_x) ** 2 + (entity.center_y - l.center_y) ** 2)
                        if dist < min_l_dist:
                            min_l_dist = dist
                            nearest_lair = l

                    if nearest_lair and min_l_dist < TILE_SIZE * 10:
                        nearest_lair.guardians_needed -= 1
                        print(f"Осталось стражей логова: {nearest_lair.guardians_needed}")

                entity.kill()
                if entity in self.heroes_list:
                    self.heroes_list.remove(entity)
                if entity in self.enemy_list:
                    self.enemy_list.remove(entity)
            elif entity.get_stat('hp')[-1] > entity.get_stat('max_hp')[0]:
                entity['hp'] = entity.get_stat('max_hp')[0] + entity.get_stat('hp')[1]

    def on_draw(self):
        self.clear()
        if self.camera:
            self.camera.use()
        self.tile_list.draw()
        self.entity_list.draw()
        for lair in self.lairs_list:
            arcade.draw_text(f"{lair.guardians_needed}", lair.center_x, lair.center_y + 50, arcade.color.RED, 14,
                             anchor_x="center")
        self.fog_list.draw()
        self.ui_camera.use()
        self.char_info_overlay.draw()

    def enemy_turn_logic(self):
        print("Враги думают...")

        # Строим карту препятствий (другие враги - препятствия)
        # Для простоты пока игнорируем динамические препятствия при поиске пути,
        # иначе они могут заблокировать друг друга в узких проходах.
        obstacles = set()
        for i in self.enemy_list:
            obstacles.add((int(i.position[0]), int(i.position[1])))
        for enemy in self.enemy_list:
            # 1. Найти ближайшего героя
            closest_hero = None
            min_dist = float('inf')

            e_gx = int(enemy.center_x // TILE_SIZE)
            e_gy = int(enemy.center_y // TILE_SIZE)

            for hero in self.heroes_list:
                h_gx = int(hero.center_x // TILE_SIZE)
                h_gy = int(hero.center_y // TILE_SIZE)
                dist = abs(e_gx - h_gx) + abs(e_gy - h_gy)
                if dist < min_dist:
                    min_dist = dist
                    closest_hero = hero

            if closest_hero:
                # 2. Построить путь BFS
                target_gx = int(closest_hero.center_x // TILE_SIZE)
                target_gy = int(closest_hero.center_y // TILE_SIZE)

                path = bfs_path((e_gx, e_gy), (target_gx, target_gy), obstacles=obstacles)

                # 3. Атака или Движение
                if len(path) <= enemy.get_stat('move_range')[0]:
                    apply_ability(enemy, closest_hero, enemy.selected_ability)
                    steps = [int(enemy.position[0]), int(enemy.position[1])]
                else:
                    # Движение
                    move_limit = enemy.get_stat('move_range')[0]
                    # Берем первые N шагов, исключая последний шаг (там герой)
                    steps = path[:move_limit]
                    if steps and steps[-1] == (target_gx, target_gy):
                        steps.pop()

                    # Заполняем очередь анимации
                    for sx, sy in steps:
                        world_x = sx * TILE_SIZE + TILE_SIZE / 2
                        world_y = sy * TILE_SIZE + TILE_SIZE / 2
                        enemy.path_queue.append((world_x, world_y))
                obstacles.add(steps[-1]) # там будет находиться враг
        # Переходим в фазу движения
        self.turn_state = ENEMY_MOVING

    def end_turn(self):
        print("Конец хода игрока.")
        # Обновление эффектов
        for entity in self.entity_list:
            entity.update_effects_turn()

        self.turn_state = ENEMY_CALCULATING

    def on_key_press(self, key, modifiers):
        # Блокировка управления во время хода врага
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
            # Проверка входа в бар
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

    def on_mouse_press(self, x, y, button, modifiers):
        if self.turn_state != PLAYER_TURN:
            return
        if not self.camera:
            return

        if button == arcade.MOUSE_BUTTON_RIGHT:
            world_point = self.camera.unproject((x, y))
            clicked = arcade.get_sprites_at_point(world_point, self.entity_list)

            if clicked:
                target = clicked[0]
                # Логика смены позиции: Left -> Right -> Left
                new_pos = "left"
                if self.char_info_overlay.visible and self.char_info_overlay.position == "left":
                    new_pos = "right"

                self.char_info_overlay.show(target, position=new_pos)
            else:
                self.char_info_overlay.hide()
            return


        world_point = self.camera.unproject((x, y))
        wx, wy = world_point[0], world_point[1]

        active_hero = self.heroes_list[self.current_unit_index] if self.heroes_list else None
        if not active_hero or active_hero.path_queue:
            return
        clicked = arcade.get_sprites_at_point((wx, wy), self.entity_list)

        if button == arcade.MOUSE_BUTTON_RIGHT:
            world_point = self.camera.unproject((x, y))
            clicked = arcade.get_sprites_at_point(world_point, self.entity_list)

            if clicked:
                target = clicked[0]
                # Логика смены позиции: Left -> Right -> Left
                new_pos = "left"
                if self.char_info_overlay.visible and self.char_info_overlay.position == "left":
                    new_pos = "right"

                self.char_info_overlay.show(target, position=new_pos)
            else:
                self.char_info_overlay.hide()
            return

        if clicked:
            target = clicked[0]
            if target in self.heroes_list:
                self.selected_unit = target
                self.current_unit_index = self.heroes_list.index(target)
            elif target.role == 'enemy':
                dist = abs(active_hero.center_x - target.center_x) + abs(active_hero.center_y - target.center_y)
                if dist // TILE_SIZE < active_hero['move_range'] and active_hero['moves_left'] > 0:
                    apply_ability(active_hero, target, active_hero.selected_ability)
                    active_hero['moves_left'] -= 1
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

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        self.char_info_overlay.on_scroll(scroll_y)
