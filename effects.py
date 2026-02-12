import arcade
from random import randint, uniform
import math

class Particle(arcade.SpriteCircle):
    """ Базовый класс для простых эффектов-точек """
    def __init__(self, x, y, color, change_x, change_y, fade_speed=5, gravity=0):
        super().__init__(radius=3, color=color)
        self.center_x = x
        self.center_y = y
        self.change_x = change_x
        self.change_y = change_y
        self.fade_speed = fade_speed
        self.gravity = gravity

    def update(self, delta_time):
        super().update()
        self.change_y -= self.gravity * delta_time
        self.center_x += self.change_x * delta_time
        self.center_y += self.change_y * delta_time
        self.alpha -= self.fade_speed
        if self.alpha <= 0:
            self.remove_from_sprite_lists()

class TextParticle(arcade.Sprite):
    """ Класс для текстовых эффектов (например, зеленые плюсики) """
    def __init__(self, x, y, text, color, change_y=1.5, fade_speed=4):
        # Создаем текстуру из текста
        texture = arcade.create_text_sprite(text, color, font_size=20).texture
        super().__init__(texture)
        self.center_x = x
        self.center_y = y
        self.change_y = change_y * 15
        self.fade_speed = fade_speed

    def update(self, delta_time):
        self.center_y += self.change_y * delta_time
        self.alpha -= self.fade_speed
        if self.alpha <= 0:
            self.remove_from_sprite_lists()

class EffectManager:
    def __init__(self):
        self.particles = arcade.SpriteList()

    def add_damage_effect(self, x, y):
        """ Красные капельки разлетаются в стороны """
        for _ in range(randint(10, 15)):
            angle = uniform(0, 2 * math.pi)
            speed = uniform(2, 5)
            p = Particle(
                x, y,
                color=arcade.color.RED,
                change_x=math.cos(angle) * speed,
                change_y=math.sin(angle) * speed,
                fade_speed=7
            )
            self.particles.append(p)

    def add_heal_effect(self, x, y):
        """ Зеленые плюсики поднимаются вверх """
        for _ in range(randint(10, 15)):
            self.particles.append(TextParticle(x + randint(-35, 35), y + randint(-35, 35),
                                               "+", arcade.color.GREEN) )

    def add_walk_effect(self, x, y):
        """ Пыль под ногами при ходьбе """
        p = Particle(
            x + uniform(-10, 10),
            y + 10,  # Чуть выше нижней части персонажа
            color=arcade.color.LIGHT_GRAY,
            change_x=uniform(-0.5, 0.5),
            change_y=uniform(0.1, 1),
            fade_speed=10
        )
        p.alpha = 150
        self.particles.append(p)

    def add_buy_effect(self, x, y):
        """ Эффект вылета монет по параболе """
        for _ in range(randint(20, 25)):
            # Монетки летят вверх под крутым углом
            angle = uniform(math.pi * 0.3, math.pi * 0.7)
            speed = uniform(4, 8)
            p = Particle(
                x, y,
                color=arcade.color.GOLD,
                change_x=math.cos(angle) * speed,
                change_y=math.sin(angle) * speed,
                fade_speed=3,  # Сделал затухание медленнее, чтобы успели упасть
                gravity=10  # Добавляем гравитацию
            )
            self.particles.append(p)

    def update(self, delta_time):
        self.particles.update(delta_time)

    def draw(self):
        self.particles.draw()