import arcade
from arcade.gui import UIManager

from constants import *


class CharacterInfoOverlay:
    def __init__(self):
        self.visible = False
        self.entity = None
        self.position = "left"
        self.scroll_y = 0
        self.padding = 35
        self.panel_width = 350
        self.update_timer = 0
        self.update_interval = 1
        self.scissor_bottom = self.padding * 1.5
        self.scissor_height = SCREEN_HEIGHT - self.padding * 3
        self.ability_buttons = []
        self.manager = UIManager()

        self.window = arcade.get_window()

        # Кешируем фон и список элементов
        self.background_texture = arcade.load_texture('images/info_panel.jpg')
        self.ui_elements = []  # Здесь будем хранить объекты arcade.Text
        self.sprite_list = arcade.SpriteList()  # Для превью
        self.panel_sprite = None

    def show(self, entity, position="left"):
        self.entity = entity
        self.visible = True
        self.position = position
        self.scroll_y = 0
        self.ability_buttons = []
        self.manager = UIManager()
        self.rebuild_ui()
        if entity.role == 'hero':
            self.manager.enable()

    def update(self, delta_time):
        if self.visible and self.entity:
            self.update_timer += delta_time
            if self.update_timer >= self.update_interval:
                self.rebuild_ui()
                self.update_timer = 0

    def hide(self):
        self.manager.disable()
        self.visible = False
        self.ui_elements.clear()
        self.sprite_list.clear()

    def rebuild_ui(self):
        self.ui_elements.clear()
        self.sprite_list.clear()

        if not self.entity:
            return

        x_start = 0 if self.position == "left" else SCREEN_WIDTH - self.panel_width
        content_x = x_start + self.padding
        current_y = SCREEN_HEIGHT - self.padding * 2

        # 1. Имя
        name_text = getattr(self.entity, 'name', self.entity.role.capitalize())
        self.ui_elements.append(arcade.Text(
            name_text, x_start + self.panel_width // 2, current_y,
            arcade.color.WHITE, 20, bold=True, anchor_x="center"
        ))
        current_y -= self.padding * 2
        # 2. Картинка (Превью) - создаем спрайт
        preview = arcade.Sprite(self.entity.texture)
        preview.center_x = x_start + self.panel_width // 2
        preview.center_y = current_y - 40
        preview.width = self.entity.width * 1.5
        preview.height = self.entity.height * 1.5
        self.sprite_list.append(preview)
        current_y -= 150

        # 3. Статы
        if self.entity.role in ('hero', 'bar_hero'):
            stats_to_show = [
                ("HP", f"{int(self.entity.get_stat('hp')[0])}/{int(self.entity.get_stat('max_hp')[0])}"),
                ("Mana", f"{int(self.entity.get_stat('mana')[0])}/{int(self.entity.get_stat('max_mana')[0])}"),
                ("AP (ОД)", f"{self.entity.get_stat('moves_left')[0]}"),
                ("Armor", f"{self.entity.get_stat('armor')[0]}"),
                ("Defense", f"{self.entity.get_stat('defense')[0]}%"),
            ]

            for label, val in stats_to_show:
                self.ui_elements.append(arcade.Text(
                    f"{label}: {val}", content_x, current_y, arcade.color.WHITE, 16
                ))
                current_y -= 25

        current_y -= 20
        # 4. Способности
        text = "Способности:" if self.entity.role != 'npc' else 'Квесты:'
        self.ui_elements.append(arcade.Text(text, content_x + 10, current_y, arcade.color.GOLD, 18))
        current_y -= 30

        if hasattr(self.entity, 'abilities'):
            for abil in self.entity.abilities:
                effect = abil.get('effect', 'None')
                name = abil.get('name', 'Unnamed')

                # Создаем кнопку через UIManager
                if len(self.ability_buttons) != len(self.entity.abilities):
                    btn = arcade.gui.UIFlatButton(text=f"• {name}",
                                                  x=content_x, y=current_y - 25,
                                                  width=self.panel_width - self.padding * 2)

                    # Добавляем логику нажатия
                    @btn.event("on_click")
                    def on_click_ability(event, eff=effect):
                        self.entity.selected_ability = eff
                        print(f"Selected: {eff}")

                    # Сохраняем начальную Y позицию в самом объекте кнопки для скролла
                    btn.base_y = btn.center_y

                    self.manager.add(btn)
                    self.ability_buttons.append(btn)

                current_y -= 50  # Отступ после кнопки

                # Эффект
                eff_text = arcade.Text(
                    f"Эффект: {abil.get('effect', 'None')}",
                    content_x, current_y, arcade.color.VIOLET, 16,
                    width=self.panel_width - 70, multiline=True
                )
                self.ui_elements.append(eff_text)
                current_y -= (eff_text.content_height + 10)

                # Описание
                desc_text = arcade.Text(
                    abil.get('description', ''),
                    content_x, current_y, arcade.color.WHITE, 14,
                    width=self.panel_width - 70, multiline=True
                )
                self.ui_elements.append(desc_text)
                current_y -= (desc_text.content_height + 20)
        # 5. Детальные параметры (База + Бафф)
        self.ui_elements.append(arcade.Text("Параметры:", content_x + 10,
                                            current_y, arcade.color.GOLD, 18))
        current_y -= 30

        for key, val in self.entity.stats_dict.items():

            base, buff = self.entity.get_stat(key)[-1], self.entity.get_stat(key)[1]

            text = f"{key}: {base}"
            if buff != 0:
                if buff > 0:
                    sign = '+'
                    color = arcade.color.GREEN
                else:
                    sign = "-"
                    color = arcade.color.RED
                text += f" {sign}{buff}"
            else:
                color = arcade.color.WHITE

            self.ui_elements.append(arcade.Text(text, content_x + 20, current_y, color, 16))

            current_y -= 20

    def on_scroll(self, scroll_y):
        if self.visible:
            self.scroll_y -= scroll_y * 20
            # Ограничение скролла
            self.scroll_y = max(0, self.scroll_y)
            self._update_button_positions()

    def _update_button_positions(self):
        """Сдвигает кнопки UIManager вслед за скроллом"""
        for btn in self.ability_buttons:
            btn.center_y = btn.base_y + self.scroll_y
            if btn.top >= SCREEN_HEIGHT - 35:
                btn.visible = False
            else:
                btn.visible = True
    def draw(self):
        if not self.visible or not self.entity or not self.sprite_list:
            return

        x = 0 if self.position == "left" else SCREEN_WIDTH - self.panel_width

        # 1. Фон
        arcade.draw_texture_rect(
            self.background_texture,
            arcade.rect.LBWH(x, 0, self.panel_width, SCREEN_HEIGHT)
        )
        self.window.ctx.scissor = (x, self.scissor_bottom, self.panel_width, self.scissor_height)
        # 2. Отрисовка элементов с учетом скролла
        prev = self.sprite_list[-1]
        original_y = prev.center_y
        prev.center_y += self.scroll_y
        if 0 < prev.bottom < SCREEN_HEIGHT:
            self.sprite_list.draw()
        prev.center_y = original_y


        for element in self.ui_elements:
            original_y = element.y
            element.y += self.scroll_y
            # Рисуем только если элемент в пределах экрана
            if 0 < element.y < SCREEN_HEIGHT:
                element.draw()
            element.y = original_y  # Возвращаем обратно
        self.manager.draw()
        self.window.ctx.scissor = None