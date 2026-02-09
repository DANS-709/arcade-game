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
    'moves_count': '3',
    'moves_left': 'moves_count',
    'view_range': '4',
    'move_range': '3',
    'attack_range': '3'}


ITEMS_DB = [{
        "name": "Меч",
        "image": "images/sword.png",
        "price": 175,
        "stats": {},
        "abilities": [
            {"name": "Удар эфесом", "effect": "target['hp'] -= 8; buff('target', 'max_hp', -5, 3)",
             "description": "Наносит 8 урона и снижает максимальное количество здоровья жертвы."}
        ]
    },
    {
        "name": "Деревянный щит",
        "image": "images/shield.png",
        "price": 75,
        "stats": {"hp": 20, "max_hp": 20},
        "abilities": []
    },{
        "name": "Зелье здоровья",
        "image": "images/potion_red.png",
        "price": 120,
        "stats": {},
        "abilities": [
            {"name": "Выпить", "effect": "hero['hp'] += 7", "description": "Восстанавливает HP."}
        ]
    }
]

NPC_DB = [
    {
        "name": "Aldric",
        "image": "images/barmen.png",
        "phrases": [
            "Поможешь нам с чудищами?",
            "Дороги стали опасны...",
            "Нужен кто-то смелый для работы."
        ],
        "final_phrases": [
        "Ты доказал, что сможешь сразиться с ним...",
        "Пришло время положить конец этому злу.",
        "Он ждёт тебя. Сразись с ним."
        ],
        "quests": [
            {
                "type": "kill_lair",
                "target": 1,          # сколько логов уничтожить
                "reward_coins": 65,
                "reward_rep": 70,
                "text": "Уничтожь одно логово поблизости."
            },
            {
                "type": "kill_enemies",
                "target": 5,          # сколько врагов
                "reward_coins": 30,
                "reward_rep": 30,
                "text": "Разберись с пятью монстрами вокруг города."
            }
        ]
    }
]

FINAL_RETURN_QUEST = {
    "type": "return_to_bar",
    "target": 1,
    "reward_coins": 0,
    "reward_rep": 0,
    "text": "Вернись в бар. Там тебя ждёт решающая битва."
}

FINAL_FIGHT_QUEST = {
    "type": "fight with boss",
    "target": 1,
    "reward_coins": 0,
    "reward_rep": 0,
    "text": "Босс призван! найди и уничтожь его."
}


BOSS_VAMPIRE = {"name": "Лорд Дракулас",
    "race": ["vampire","hero['move_range'] = 6"],
    "class": ["boss", "hero['attack_range'] = 2"],
    "stats": {"dexterity": 12, "strength": 5, "intelligence": 6, "charisma": 2},
    "level": 1,
    "hp": 1,  # в игре поменяем на сумму хп всех героев * 2
    "abilities": [
        {"name": "Кровавый укус",
         "effect": "target['hp'] -= hero['dexterity'] - target['strength'];hero['hp'] += 5;buff('hero', 'max_hp' 2, 2)",
         "description": "Кусает противника"},
        {"name": "Облако летучих мышей",
         "effect": "buff('target', 'hp', -10, 1);buff('target', 'max_hp', -6, 4)",
         "description": "Атакует противника стаей летучих мышей, уменьшая его максимальный запас здоровья"},
        {"name": "Тёмное проклятие",
        "effect": "target['hp'] -= hero['intelligence'] + hero['charisma'];buff('target', 'move_range', -2, 2)",
        "description": "Проклинает врага, замедляя его"
        },
    ],
    "image_b64": ""
}


GUARD_JSON = {
    "name": "guard",
    "race": ["ancient","hero['move_range'] = 5"],
    "class": ["protector", "buff('hero', 'hp', 3, 3)"],
    "stats": {"dexterity": 2, "strength": 7, "intelligence": 6, "charisma": -3},
    "level": 1,
    "hp": 12,
    "abilities": [
        {"name": "обычный удар", "effect": "target['hp'] -= 1 + d4; buff('hero', 'hp', 1, 2)",
         "description": "Наносит урон врагу, получая небольшой бафф."},
        {"name": "Удар с воздуха",
         "effect": "buff('target', 'max_hp', -3, 2);target['hp'] -= 7;hero['hp'] -= 5; buff('hero', 'hp', -2, 1)",
         "description": "взлетает вверх, после чего падает на противника"}
    ],
    "image_b64": ""  # Пусто, загрузится дефолтная
}
ENEMY_JSON = {"name": "spooky scary sceleton",
    "race": ["sceleton","buff('hero', 'move_range', -1, 2)"],
    "class": ["warrior","buff('hero', 'hp', -3, 2)"],
    "stats": {"dexterity": -2, "strength": 1, "intelligence": 2, "charisma": -3},
    "level": 1,
    "hp": 10,
    "abilities": [
        {"name": "удар мечом", "effect": "target['hp'] -= 4 + hero['dexterity'] + hero['strength']",
         "description": "Наносит рубящий удар мечом по врагу."}
    ],
    "image_b64": "" } # Пусто, загрузится дефолтная