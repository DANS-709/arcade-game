# --- НАСТРОЙКИ ЭКРАНА ---
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800
SCREEN_TITLE = "D&D Arcade RPG"

# --- НАСТРОЙКИ МИРА ---
TILE_SIZE = 120
GRID_WIDTH = 50
GRID_HEIGHT = 50

# --- СКОРОСТИ ---
CAMERA_SPEED = 30
ENEMY_MOVE_SPEED = 15
PLAYER_BAR_SPEED = 5  # Скорость движения в баре (WASD)

# --- СОСТОЯНИЯ ХОДА ---
PLAYER_TURN = 0
ENEMY_CALCULATING = 1
ENEMY_MOVING = 2

# --- ПАРАМЕТРЫ ПЕРСОНАЖА ПО УМОЛЧАНИЮ ---
# Словарь соответствия для инициализации
EXTEND_PARAMS = {
    'max_hp': 'max_hp',
    'hp': 'max_hp',
    'max_mana': '100',
    'mana': 'max_mana',
    'moves_count': '3',
    'moves_left': 'moves_count',
    'damage_deal': '0',
    'view_range': '4',
    'move_range': '4',
    'attack_range': '3',
    'armor': '0',      # Плоская защита (вычитается из урона)
    'defense': '0'     # Процентная защита (снижает урон на %)
}

GUARD_JSON = {
    "name": "guard",
    "race": ["ancient","hero['moves_range'] = 6"],
    "class": ["protector", "buff(hero, 'hp', 10, 5); hero['armor'] = 2"],
    "stats": {"dex": 2, "str": 1, "int": 6, "cha": 7},
    "level": 1,
    "hp": 30,
    "abilities": [
        {"name": "обычный удар", "effect": "target['hp'] -= 3; buff('hero', 'hp', 1, 2)",
         "description": "Наносит урон врагу, получая небольшой бафф."},
        {"name": "Удар с воздуха",
         "effect": "buff('target', 'max_hp', -3, 2);target['hp'] -= 7;hero['hp'] -= 5; buff('hero', 'hp', -2, 1)",
         "description": "взлетает вверх, после чего падает на противника"}
    ],
    "image_b64": ""  # Пусто, загрузится дефолтная
}
ENEMY_JSON = {"name": "spooky scary sceleton",
    "race": ["sceleton","buff('hero', 'move_range', -1, 2)"],
    "class": ["warrior","buff('hero', 'hp', -5, 2)"],
    "stats": {"dex": 2, "str": 1, "int": 2, "cha": -3},
    "level": 1,
    "hp": 15,
    "abilities": [
        {"name": "удар мечом", "effect": "target['hp'] -= 3", "description": "Наносит рубящий удар мечом по врагу."}
    ],
    "image_b64": "" } # Пусто, загрузится дефолтная}