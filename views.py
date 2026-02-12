import datetime
import arcade
from entities import NPC
from arcade.gui import UIManager
from arcade.gui.widgets.layout import UIAnchorLayout
import random
import math
from llm import ask_npc
from perlin_noise import PerlinNoise
from constants import *
from entities import Entity, Lair, ShopItem
from game_logic import bfs_path, apply_ability, load_characters_from_zip
from ui import CharacterInfoOverlay
from effects import EffectManager
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
            cls.win_image = arcade.load_texture('images/win.png')
        except:
            pass
        # Загрузка звуков (заглушки при ошибке)
        try:
            cls.start_music = arcade.load_sound('sound/Dota_2_-_Main_Menu_Flute_Theme_75018976.mp3')
            cls.lose_music = arcade.load_sound('sound/Giulio-Fazio-Wandering-Knight_lose_misic.mp3')
            cls.game_music = arcade.load_sound('sound/backgound_witcher.mp3')
            cls.bar_music = arcade.load_sound('sound/tavern_witcher.mp3')
            cls.win_sound = arcade.load_sound('sound/mixkit-medieval-show-fanfare-announcement-226.wav')
            cls.click_sound = arcade.load_sound('sound/click.mp3')
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
        try:
            conn = database.get_connection()
            cursor = conn.cursor()
            cursor.execute("""SELECT name, image_path, price, stats_json, abilities_json FROM items""")
            rows = cursor.fetchall()
            ITEMS_DB = []
            for row in rows:
                ITEMS_DB.append({'name': row[0], 'image_path': row[1], 'price': row[2],
                                 'stats_json': row[3], 'abilities': row[4]})
            conn.close()

        except:
            pass

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
        self.select_save= False

    def on_click_continue(self, event):
        self.select_save = True
        ResourceManager.click_sound.play()
        self.manager.disable()
        self.window.show_view(SaveListView(self, self.current_frame))


    def on_click_new_game(self, event):
        self.manager.disable()
        ResourceManager.click_sound.play()
        if not self.input_text.text.strip():
            self.input_text.text = 'Название некорректно'
        elif len(self.input_text.text) > 15:
            self.input_text.text = 'В названии >15 символов'
        else:
            game_view = GameView(self.input_text.text.strip())
            game_view.setup(load_data=None)  # Новая игра
            if game_view.success:
                arcade.stop_sound(self.start_player)
                self.window.show_view(game_view)
                return
        self.input_text._border_color = arcade.color.RED
        self.manager.enable()

    def on_click_quit(self, event):
        arcade.exit()

    def on_show_view(self):
        if not self.select_save:
            self.start_player = ResourceManager.start_music.play(loop=True)
            arcade.set_background_color(arcade.color.BLACK)
        self.manager.enable()

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
        self.v_box = arcade.gui.UIBoxLayout(space_between=10)

        button_style = {
            "normal": {"font_name": ("Arial",), "font_size": 16, "font_color": arcade.color.LIME_GREEN},
            "hover": {"font_name": ("Arial",), "font_size": 16, "font_color": arcade.color.MALACHITE},
            "press": {"font_name": ("Arial",), "font_size": 16, "font_color": arcade.color.MALACHITE}
        }

        self.v_box.add(arcade.gui.UILabel(text="Введите название мира:", font_size=16))
        self.input_text = arcade.gui.UIInputText(width=225, height=30, border_color=arcade.color.MALACHITE)
        self.v_box.add(self.input_text)

        continue_btn = arcade.gui.UITextureButton(text="Продолжить", width=225,
                                                  texture=ResourceManager.button,
                                                  texture_hovered=ResourceManager.hover_button,
                                                  style=button_style)
        continue_btn.place_text(align_x=10)
        continue_btn.on_click = self.on_click_continue
        self.v_box.add(continue_btn)

        new_game_btn = arcade.gui.UITextureButton(text="Новая Игра", width=225,
                                                  texture=ResourceManager.button,
                                                  texture_hovered=ResourceManager.hover_button,
                                                  style=button_style)
        new_game_btn.on_click = self.on_click_new_game
        continue_btn.place_text(align_x=10)
        self.v_box.add(new_game_btn)

        quit_btn = arcade.gui.UITextureButton(text="Выход", width=225,
                                              texture=ResourceManager.button,
                                              texture_hovered=ResourceManager.hover_button,
                                              style=button_style)
        quit_btn.on_click = self.on_click_quit
        self.v_box.add(quit_btn)

        self.anchor_layout.add(anchor_x="left", anchor_y="center_y", align_x=55, align_y=-50, child=self.v_box)

class SaveListView(arcade.View):
    def __init__(self, main_menu_view, cur_frame):
        super().__init__()
        self.main_menu_view = main_menu_view
        self.manager = arcade.gui.UIManager()
        self.manager.enable()
        self.v_box = arcade.gui.UIBoxLayout(space_between=10)

        # Стиль кнопок
        button_style = {
            "normal": {"font_name": ("Arial",), "font_size": 14, "font_color": arcade.color.WHITE},
            "hover": {"font_name": ("Arial",), "font_size": 14, "font_color": arcade.color.LIME_GREEN},
            "press": {"font_name": ("Arial",), "font_size": 14, "font_color": arcade.color.MALACHITE}
        }

        # Получаем данные из БД
        saves = database.get_recent_saves()

        if not saves:
            self.v_box.add(arcade.gui.UILabel(text="НЕТ СОХРАНЕНИЙ", font_size=42, text_color=arcade.color.RUBY))
        else:
            for s_id, name, time_str in saves:
                # Создаем кнопку для каждого сохранения
                btn_text = f"{name}({time_str})"
                btn = arcade.gui.UITextureButton(text=btn_text, width=435, height=100,
                                                 texture=ResourceManager.button,
                                                 texture_hovered=ResourceManager.hover_button,
                                                 style=button_style)
                btn.place_text(anchor_x='right', align_x=-25)

                @btn.event("on_click")
                def on_click_save(event, save_id=s_id, name=name, time=time_str):
                    self.load_game(save_id, name, time)

                self.v_box.add(btn)
        # Кнопка Назад
        back_btn = arcade.gui.UITextureButton(text="Назад", width=200,
                                              texture=ResourceManager.button,
                                              texture_hovered=ResourceManager.hover_button,
                                              style=button_style)
        back_btn.on_click = self.on_click_quit
        self.v_box.add(back_btn)

        # Центрируем всё
        self.anchor = arcade.gui.UIAnchorLayout()
        self.anchor.add(anchor_x="center_x", anchor_y="center_y", child=self.v_box)
        self.manager.add(self.anchor)
        self.anim_timer = 0
        self.current_frame = cur_frame

    def on_click_quit(self, event):
        self.manager.disable()
        self.window.show_view(self.main_menu_view)

    def load_game(self, save_id, name, time):
        data = database.load_game_state(save_id)
        ResourceManager.click_sound.play()
        if data:
            self.manager.disable()
            game_view = GameView(name, time)
            game_view.setup(load_data=data)
            arcade.stop_sound(self.main_menu_view.start_player)
            self.main_menu_view.select_save = False
            self.window.show_view(game_view)

    def on_show_view(self):
        arcade.set_background_color(arcade.color.BLACK)

    def on_draw(self):
        self.clear()
        if ResourceManager.start_frames:
            texture = ResourceManager.start_frames[self.current_frame]
            arcade.draw_texture_rect(texture, arcade.rect.LBWH(0, 0, self.width, self.height))
        self.manager.draw()
    def on_update(self, delta_time):
        if ResourceManager.start_frames:
            self.anim_timer += delta_time
            if self.anim_timer > 0.065:
                self.anim_timer = 0
                self.current_frame = (self.current_frame + 1) % len(ResourceManager.start_frames)
                self.main_menu_view.current_frame = (self.current_frame + 1) % len(ResourceManager.start_frames)

class GameEndView(arcade.View):
    def __init__(self, win=False):
        super().__init__()
        self.view_camera = arcade.camera.Camera2D()
        self.current_frame = 0
        self.win = win
        self.anim_timer = 0.0


    def on_show_view(self):
        if not self.win:
            self.player = ResourceManager.lose_music.play(loop=True, speed=0.75)
        else:
            self.player = ResourceManager.win_sound.play(volume=0.75)
        arcade.set_background_color(arcade.color.BLACK)

    def on_update(self, delta_time):
        if ResourceManager.lose_frames and not self.win:
            self.anim_timer += delta_time
            if self.anim_timer > 0.05:
                self.anim_timer = 0
                self.current_frame = (self.current_frame + 1) % len(ResourceManager.lose_frames)

    def on_draw(self):
        self.clear()
        self.view_camera.use()
        if ResourceManager.lose_frames and not self.win:
            texture = ResourceManager.lose_frames[self.current_frame]
            arcade.draw_texture_rect(texture, arcade.rect.LBWH(0, 0, self.width, self.height))
        elif self.win:
            arcade.draw_texture_rect(ResourceManager.win_image,
                                     arcade.rect.LBWH(0, 0, self.width, self.height))
        else:
            arcade.draw_text("GAME END",
                             SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, arcade.color.RED, 50, anchor_x="center")

    def on_key_press(self, symbol, modifiers):
        arcade.stop_sound(self.player)
        self.window.show_view(StartView())

class BarView(arcade.View):
    """ Локация Бара с физикой """

    def __init__(self, game_view):
        super().__init__()
        self.game_view = game_view
        self.items_list = arcade.SpriteList()
        self.all_list = arcade.SpriteList()
        self.ui_overlay = game_view.char_info_overlay
        self.clicks = 0

        self.scene = None
        self.player_sprite = None
        self.physics_engine = None
        self.camera = None
        self.scale = 3.2
        self.effect_manager = EffectManager()
        self.map_width = 15 * (30 * self.scale)
        self.map_height = 10 * (30 * self.scale)

        arcade.set_background_color(arcade.color.BLACK)

    def setup(self):
        self.camera = arcade.camera.Camera2D()

        # Пытаемся загрузить карту
        try:
            self.tile_map = arcade.load_tilemap("maps/bar.tmx", scaling=self.scale, use_spatial_hash=True)
            self.scene = arcade.Scene.from_tilemap(self.tile_map)

            # Ищем слой объектов с именем "items" в Tiled
            items_layer = [*self.scene.get_sprite_list('items')]
            if items_layer:
                for i, tile_obj in enumerate(items_layer):
                    try:
                        data = ITEMS_DB[i]
                        item = ShopItem(data, tile_obj.center_x, tile_obj.center_y, self.scale)
                        self.items_list.append(item)
                        self.all_list.append(item)
                    except:  # Если мест под предметы больше, чем самих предметов
                        pass
        except Exception as e:
            print(f"Ошибка загрузки карты бара: {e}.")
            arcade.stop_sound(self.bar_player)
            self.window.show_view(self.game_view)
            return
        self.scene.add_sprite_list("ShopItems", sprite_list=self.items_list)

        self.npc_list = arcade.SpriteList()

        if "npc" in self.scene._name_mapping:
            npc_layer = [*self.scene.get_sprite_list("npc")]
            for i, tile_obj in enumerate(npc_layer):
                try:
                    data = NPC_DB[i]
                    npc = NPC(data, tile_obj.center_x, tile_obj.center_y, self.scale)
                    self.npc_list.append(npc)
                    self.all_list.append(npc)
                except:
                    pass

        self.scene.add_sprite_list("NPCs", sprite_list=self.npc_list)

        self.near_npc = None
        self.npc_phrase = ''

        # Игрок
        self.player_sprite = Entity(self.game_view.selected_unit.image_path,'bar_hero',
                             stats_dict=self.game_view.selected_unit.stats_dict)
        self.player_sprite.name = self.game_view.selected_unit.name
        self.player_sprite.active_effects = self.game_view.selected_unit.active_effects
        self.player_sprite.abilities = self.game_view.selected_unit.abilities
        self.player_sprite.width, self.player_sprite.height = (90, 90)
        self.player_sprite.center_x = 200
        self.player_sprite.center_y = 200
        self.scene.add_sprite("Player", self.player_sprite)
        self.all_list.append(self.player_sprite)

        # Физика
        self.physics_engine = arcade.PhysicsEngineSimple(self.player_sprite,
            walls=[self.scene["collisions"], self.items_list, self.npc_list])

    def on_show_view(self):
        self.bar_player = ResourceManager.bar_music.play(volume=0.55,loop=True)

    def on_draw(self):
        self.clear()
        self.camera.use()
        self.scene.draw()
        if self.near_npc and self.npc_phrase:
            text = self.npc_phrase
            padding = 10
            font_size = 14

            # Размер текста
            text_width = arcade.create_text_sprite(text, arcade.color.BLACK, font_size).width
            text_height = font_size + 4

            x = self.near_npc.center_x
            y = self.near_npc.top + 20

            # Белый фон
            arcade.draw_rect_filled(arcade.rect.XYWH(
                x,
                y,
                text_width + padding * 2,
                text_height + padding,
            ), arcade.color.WHITE)

            # Текст
            arcade.draw_text(
                text,
                x,
                y,
                arcade.color.BLACK,
                font_size,
                anchor_x="center",
                anchor_y="center"
            )
        self.effect_manager.draw()

        # Рисуем ценники над предметами
        for item in self.items_list:
            arcade.draw_text(
                f"{item.price}$",
                item.center_x,
                item.top + 10,
                arcade.color.GOLD,
                24,
                anchor_x="center"
            )

        # Рисуем UI поверх всего
        self.game_view.ui_camera.use()
        # Отображаем текущее золото игрока
        coins = getattr(self.game_view, 'coins', 0)
        arcade.draw_text(f"Золото: {coins}", SCREEN_WIDTH - 20, SCREEN_HEIGHT - 20,
                         arcade.color.GOLD, 20, anchor_x="right", anchor_y="top")

        if self.game_view.active_quest:
            q = self.game_view.active_quest
            arcade.draw_text(
                f"Квест: {q['text']} ({q['progress']}/{q['target']})",
                x=SCREEN_WIDTH // 2, y=SCREEN_HEIGHT - 40,
                width=250, multiline=True, font_size=24, anchor_x='center'
            )

        self.ui_overlay.draw()


    def on_update(self, delta_time):
        self.physics_engine.update()
        self.player_sprite.center_x = max(self.player_sprite.width // 2, min(self.player_sprite.center_x,
                                                                             self.map_width - self.player_sprite.width // 2))
        self.player_sprite.center_y = max(self.player_sprite.height // 2, min(self.player_sprite.center_y,
                                                                              self.map_height - self.player_sprite.height // 2))
        self.effect_manager.update(delta_time)
        # Слежение камеры с ограничением
        new_camera_x = max(self.camera.viewport_width // 2,
                           min(self.player_sprite.center_x, self.map_width - self.camera.viewport_width // 2))
        new_camera_y = max(self.camera.viewport_height // 2,
                           min(self.player_sprite.center_y, self.map_height - self.camera.viewport_height // 2))

        self.camera.position = (new_camera_x, new_camera_y)

        if self.ui_overlay.visible:
            self.ui_overlay.update(delta_time)
    def on_mouse_press(self, x, y, button, modifiers):

        # Преобразуем координаты мыши в координаты мира
        world_point = self.camera.unproject((x, y))

        # Просмотр информации (ПКМ)
        if button == arcade.MOUSE_BUTTON_RIGHT:
            # Проверяем клик по предметам
            clicked = arcade.get_sprites_at_point(world_point, self.all_list)
            if clicked:
                self.clicks = (self.clicks + 1) % 2
                self.ui_overlay.show(clicked[0], position=["left","right"][self.clicks])
            else:
                self.ui_overlay.hide()

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        self.ui_overlay.on_scroll(scroll_y)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.W:
            self.player_sprite.change_y = PLAYER_BAR_SPEED
        elif key == arcade.key.S:
            self.player_sprite.change_y = -PLAYER_BAR_SPEED
        elif key == arcade.key.A:
            self.player_sprite.change_x = -PLAYER_BAR_SPEED
        elif key == arcade.key.D:
            self.player_sprite.change_x = PLAYER_BAR_SPEED
        if key == arcade.key.E:
            closest_npc = arcade.get_closest_sprite(self.player_sprite, self.npc_list)
            if closest_npc:
                npc, dist = closest_npc
                if dist < (30 * self.scale) * 1.3:
                    self.start_dialog(npc)
                    return
            # Ищем предметы рядом с игроком
            closest_item = arcade.get_closest_sprite(self.player_sprite, self.items_list)
            if closest_item:
                item, dist = closest_item
                if dist < (30 * self.scale) * 1.3:  # Если стоим рядом
                    cost = item.price
                    current_coins = getattr(self.game_view, 'coins', 0)

                    if current_coins >= cost:
                        self.game_view.coins = current_coins - cost
                        buyer = self.game_view.selected_unit
                        if buyer:
                            self.effect_manager.add_buy_effect(item.center_x, item.center_y)
                            self.player_sprite.equip_item(item)  # применяем к временному персонажу в баре
                            buyer.equip_item(item)  # применяем к основному персонажу
                            print("Предмет куплен!")
                            # Удаляем предмет
                            item.remove_from_sprite_lists()
                            self.ui_overlay.hide()
                    else:
                        print("Недостаточно золота!")
        elif key == arcade.key.ESCAPE:
            # Выход из бара
            self.ui_overlay.hide()
            arcade.stop_sound(self.bar_player)
            self.window.show_view(self.game_view)


    def on_key_release(self, key, modifiers):
        if key in [arcade.key.W, arcade.key.S]:
            self.player_sprite.change_y = 0
        elif key in [arcade.key.A, arcade.key.D]:
            self.player_sprite.change_x = 0

    def start_dialog(self, npc):
        # Минимальный вариант: print + ввод через консоль
        print(f"Вы разговариваете с {npc.name}")
        self.active_npc = npc
        while True:
            mesg = input()
            if mesg == '':
                break
            self.send_player_message(input())


    def send_player_message(self, text):
        npc = self.active_npc
        system_prompt = npc.build_prompt(self.game_view.selected_unit)
        reply = ask_npc(system_prompt, text)

        print(f"{npc.name}: {reply}")


class GameView(arcade.View):
    def __init__(self, name='not_named', time=''):
        super().__init__()
        self.map_seed = None  # Для сохранения
        self.tile_list = None
        self.entity_list = None
        self.effect_manager = EffectManager()
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
        self.name = name
        self.time_of_creation = time
        arcade.set_background_color(arcade.color.BLACK)

    def on_show_view(self):
        self.background_music_player = ResourceManager.game_music.play(volume=0.4, loop=True)

    def setup(self, load_data=None):
        self.tile_list = arcade.SpriteList()
        self.entity_list = arcade.SpriteList()
        self.enemy_list = arcade.SpriteList()
        self.heroes_list = arcade.SpriteList()
        self.fog_list = arcade.SpriteList()
        self.towns = arcade.SpriteList()
        self.forests = arcade.SpriteList()
        self.ui_camera = arcade.camera.Camera2D()
        self.char_info_overlay = CharacterInfoOverlay()
        self.coins = 75
        self.active_quest = None
        self.reputation = 0
        self.boss_spawned = False
        self.boss_entity = None
        self.final_quest_unlocked = False
        self.lairs_list = []
        self.camera = arcade.camera.Camera2D()

        # 1. Генерация карты (из сохранения или новая)
        if load_data:
            self.map_seed = load_data['world']['seed']
            self.coins = load_data['world']['coins']
            self.reputation = load_data['world']['rep']
            self.active_quest = load_data['world']['quest']

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
                    if tile_type in ('bar', 'town'):
                        self.towns.append(tile)
                    elif tile_type == 'forest':
                        self.forests.append(tile)
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

        # 2. Загрузка сущностей
        if load_data:
            # Восстанавливаем сущности из БД
            for ent_data in load_data['entities']:
                if ent_data['role'] == 'hero':
                    hero = Entity(ent_data['image_path'], "hero", stats_dict=ent_data['stats'])
                    hero.name = ent_data['name']
                    hero.active_effects = ent_data['effects']
                    hero.abilities = ent_data['abilities']
                    hero.inventory = ent_data['inventory']
                    hero.center_x, hero.center_y = ent_data['x'], ent_data['y']
                    self.entity_list.append(hero)
                    self.heroes_list.append(hero)
                else:
                    is_guardian = ent_data['is_guardian']
                    enemy = Entity(ent_data['image_path'], "enemy", stats_dict=ent_data['stats'])
                    enemy.name = ent_data['name']
                    enemy.active_effects = ent_data['effects']
                    enemy.abilities = ent_data['abilities']
                    enemy.inventory = ent_data['inventory']
                    enemy.is_guardian = is_guardian
                    enemy.is_boss = ent_data['is_boss']
                    if enemy.is_boss:
                        self.boss_entity = enemy
                        self.boss_spawned = True
                        self.active_quest = FINAL_FIGHT_QUEST
                        self.active_quest['progress'] = 0
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
            if not valid_spawn_tiles: valid_spawn_tiles.append(self.tile_list[GRID_WIDTH + GRID_WIDTH // 2])
            spawn_point = random.choice(valid_spawn_tiles)
            heroes = load_characters_from_zip()
            if not heroes:
                self.success = False
                return
            self.success = True
            self.time_of_creation = str(datetime.datetime.now())[:-7]
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
                    if arcade.get_sprites_at_point(l_pos, self.towns):
                        continue
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
                        print(f"Противник использует способность:\n{enemy.selected_ability.get('name', '')}")
                        apply_ability(enemy, closest_hero,
                                      enemy.selected_ability.get('effect', 'The entity does not have any abilities'),
                                      self.effect_manager)
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
            database.save_game_state({'seed':self.map_seed, 'name': self.name,
                                      'time_of_creation': self.time_of_creation,
                                      'coins': self.coins, 'rep': self.reputation, 'quest': self.active_quest},
                                     self.heroes_list, self.enemy_list, self.lairs_list)
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
        elif key == arcade.key.ESCAPE:
            arcade.stop_sound(self.background_music_player)
            self.window.show_view(StartView())

    def on_key_release(self, key, modifiers):
        if key in [arcade.key.UP, arcade.key.DOWN]:
            self.camera_vel[1] = 0
        if key in [arcade.key.LEFT, arcade.key.RIGHT]:
            self.camera_vel[0] = 0

    def on_update(self, delta_time):
        if len(self.heroes_list) == 0:
            arcade.stop_sound(self.background_music_player)
            self.window.show_view(GameEndView())
            return
        if self.char_info_overlay.visible:
            self.char_info_overlay.update(delta_time)

        self.effect_manager.update(delta_time)
        # Эффект ходьбы
        for entity in self.entity_list:
            # Обновляем логику рывков и тряски
            entity.update_animation_logic(delta_time)
            if hasattr(entity, 'path_queue') and entity.path_queue:
                self.effect_manager.add_walk_effect(entity.center_x, entity.bottom)


        if self.turn_state == ENEMY_CALCULATING:
            self.enemy_turn_logic()
        elif self.turn_state == ENEMY_MOVING:
            any_moving = False
            for enemy in self.enemy_list:
                enemy.update_position()
                if enemy.is_moving:
                    any_moving = True
            if not any_moving:
                self.turn_state = PLAYER_TURN
                for unit in self.heroes_list:
                    unit['moves_left'] = unit.get_stat('moves_count')[0]
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
                        if ((dx == 0 and dy == 0) or arcade.get_sprites_at_point(
                                ((lx + dx) * TILE_SIZE + 40, (ly + dy) * TILE_SIZE + 40), self.entity_list)):
                            continue
                        self.spawn_enemy(lx + dx, ly + dy, is_guardian=True)
                        c += 1

            if lair.guardians_needed <= 0:
                lair.kill()
                self.lairs_list.remove(lair)
                self.coins += 30
                if self.active_quest and self.active_quest["type"] == "kill_lair":
                    self.active_quest["progress"] += 1
                    self.check_quest_complete()

        # Смерть
        for entity in self.entity_list:
            if entity.get_stat('hp')[0] <= 0:
                if entity == self.boss_entity or getattr(entity, 'is_boss', False):
                    print("Босс повержен. Игра окончена.")
                    arcade.stop_sound(self.background_music_player)
                    self.window.show_view(GameEndView(win=True))
                    return
                if getattr(entity, 'is_guardian', False):
                    n_lair, min_d = None, float('inf')
                    for l in self.lairs_list:
                        d = math.sqrt((entity.center_x - l.center_x) ** 2 + (entity.center_y - l.center_y) ** 2)
                        if d < min_d:
                            min_d = d; n_lair = l
                    if n_lair:
                        n_lair.guardians_needed -= 1

                if entity in self.heroes_list:
                    self.heroes_list.remove(entity)
                    self.coins -= self.coins // len(self.heroes_list) if len(self.heroes_list) > 0 else 0
                if entity in self.enemy_list:
                    self.enemy_list.remove(entity)
                    self.coins += 10 if getattr(entity, 'is_guardian', False) else 5
                    if self.active_quest and self.active_quest["type"] == "kill_enemies":
                        self.active_quest["progress"] += 1
                        self.check_quest_complete()
                entity.kill()
            elif entity['hp'] > entity.get_stat('max_hp')[0]:
                entity['hp'] = entity.get_stat('max_hp')[0]

    def on_draw(self):
        self.clear()
        if self.camera:
            self.camera.use()
        self.tile_list.draw()
        self.entity_list.draw()
        for lair in self.lairs_list:
            arcade.draw_text(f"{lair.guardians_needed}", lair.center_x, lair.center_y + 50, arcade.color.RED, 14,
                             anchor_x="center")
        if self.selected_unit:
            arcade.draw_rect_outline(arcade.rect.XYWH(
                self.selected_unit.center_x,
                self.selected_unit.center_y,
                self.selected_unit.width,
                self.selected_unit.height,
            ), color=arcade.color.WHITE, border_width=3)
        self.effect_manager.draw()
        self.fog_list.draw()
        if self.active_quest:
            q = self.active_quest
            arcade.draw_text(
                f"Квест: {q['text']} ({q['progress']}/{q['target']})",
                x=self.camera.position[0], y=self.camera.position[1] + SCREEN_HEIGHT // 2 - 40,
                width=250, multiline=True, font_size=24, anchor_x='center'
            )
        arcade.draw_text(
            f"Монеты: {self.coins}",
            x=self.camera.position[0], y=self.camera.position[1] - SCREEN_HEIGHT // 2 + 25, color=arcade.color.GOLD,
            font_size=24, anchor_x='center'
        )
        arcade.draw_text(
            f"Репутация: {self.reputation}",
            x=self.camera.position[0], y=self.camera.position[1] - SCREEN_HEIGHT // 2 + 60,
            color=arcade.color.RED if self.reputation < 35 else arcade.color.GREEN,
            font_size=24, anchor_x='center'
        )
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

    def spawn_boss(self):
        if self.boss_spawned:
            return

        total_hp = sum(h.get_stat('max_hp')[0] for h in self.heroes_list)
        boss_data = BOSS_VAMPIRE.copy()
        boss_data["hp"] = total_hp * 2

        boss = Entity("images/vampire.png", "enemy", json_data=boss_data)
        boss.is_guardian = False
        boss.is_boss = True

        # Ставим в рандомный лес
        boss.position = random.choice(self.forests).position
        self.active_quest = FINAL_FIGHT_QUEST
        self.active_quest['progress'] = 0
        self.entity_list.append(boss)
        self.enemy_list.append(boss)

        self.boss_entity = boss
        self.boss_spawned = True
        print("Босс появился:", boss_data.get("name"))

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        self.char_info_overlay.on_scroll(scroll_y)

    def end_turn(self):
        print("Конец хода игрока.")
        for entity in self.entity_list:
            entity.update_effects_turn()
            entity['mana'] = entity.get_stat('max_mana')[0]
        for lair in self.lairs_list:
            lair.next_spawn_interval -= 1
            if lair.next_spawn_interval <= 0:
                lair.next_spawn_interval = random.randint(*lair.spawn_interval)
                lx, ly = int(lair.center_x // TILE_SIZE), int(lair.center_y // TILE_SIZE)
                print('Вышли бродячие монстры!')
                c = 0
                for sx in range(-2, 2):
                    for sy in range(-2, 2):
                        if (not (arcade.get_sprites_at_point(((lx + sx) * TILE_SIZE + 42,
                                                              (ly + sy) * TILE_SIZE + 42),
                                                             self.entity_list)) and sx != 0 and sy != 0):
                            if c < 3:
                                self.spawn_enemy(lx + sx, ly + sy)
                                c += 1
        self.turn_state = ENEMY_CALCULATING

    def check_quest_complete(self):
        q = self.active_quest
        if not q:
            return
        if q["progress"] >= q["target"]:
            print("Квест выполнен:", q["text"])
            self.coins += q["reward_coins"]
            self.reputation += q["reward_rep"]
            print(f"Награда: {q['reward_coins']} золота, {q['reward_rep']} репутации")
            # Если репутация стала больше 100 — открываем финальный квест
            if self.reputation > 100 and not self.final_quest_unlocked:
                self.final_quest_unlocked = True
                self.active_quest = FINAL_RETURN_QUEST
                self.active_quest["progress"] = 0
                print("Открыт финальный квест: Вернуться в бар")
            else:
                self.active_quest = None

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
            dist = abs(active_hero.center_x - target.center_x) + abs(active_hero.center_y - target.center_y)
            if target in self.heroes_list:
                if not self.selected_unit.selected_ability:
                    self.selected_unit = target
                    self.current_unit_index = self.heroes_list.index(target)
                elif (dist // TILE_SIZE <= active_hero.get_stat('attack_range')[0]
                      and active_hero.get_stat('moves_left')[0] > 0):
                    apply_ability(self.selected_unit, target, self.selected_unit.selected_ability, self.effect_manager)
                    active_hero['moves_left'] -= 1
            elif target.role == 'enemy':
                if (dist // TILE_SIZE <= active_hero.get_stat('attack_range')[0]
                        and active_hero.get_stat('moves_left')[0] > 0):
                    if active_hero.selected_ability:
                        apply_ability(active_hero, target, active_hero.selected_ability, self.effect_manager)
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
        self.selected_unit.selected_ability = None  # убираем выбранную способность (уже использовали или пошли)
        if all(u.get_stat('moves_left')[0] <= 0 for u in self.heroes_list):
            self.end_turn()