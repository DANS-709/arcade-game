import sqlite3
import json
import os


DB_NAME = "gamedata.db"


def init_db():
    """ Создает таблицы, если их нет """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Таблица для глобальных настроек (сид карты)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS game_state (
            id INTEGER PRIMARY KEY,
            map_seed INTEGER
        )
    ''')

    # Таблица сущностей (Герои и Враги)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT,
            x REAL,
            y REAL,
            stats_json TEXT,
            effects_json TEXT,
            abilities_json TEXT,
            is_guardian INTEGER,
            image_path TEXT
        )
    ''')

    # Таблица логов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lairs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            x REAL,
            y REAL,
            guardians_needed INTEGER,
            next_spawn_interval REAL,
            guardians_spawned INTEGER
        )
    ''')

    conn.commit()
    conn.close()


def save_game_state(seed, heroes, enemies, lairs):
    """ Сохраняет текущее состояние игры """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. Очищаем старые сохранения (для прототипа храним только 1 слот)
    cursor.execute('DELETE FROM game_state')
    cursor.execute('DELETE FROM entities')
    cursor.execute('DELETE FROM lairs')

    # 2. Сохраняем сид
    cursor.execute('INSERT INTO game_state (map_seed) VALUES (?)', (seed,))
    # 3. Сохраняем сущностей
    all_entities = [*heroes, *enemies]
    for entity in all_entities:
        stats = json.dumps(entity.stats_dict)
        effects = json.dumps(entity.active_effects)
        abilities = json.dumps(entity.abilities)
        is_guardian = 1 if getattr(entity, 'is_guardian', False) else 0

        cursor.execute('''
            INSERT INTO entities (role, x, y, stats_json, effects_json, abilities_json, is_guardian, image_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (entity.role, entity.center_x, entity.center_y,
              stats, effects, abilities, is_guardian, entity.image_path))

    # 4. Сохраняем логова
    for lair in lairs:
        cursor.execute('''
            INSERT INTO lairs (x, y, guardians_needed, next_spawn_interval, guardians_spawned)
            VALUES (?, ?, ?, ?, ?)
        ''', (lair.center_x, lair.center_y, lair.guardians_needed, lair.next_spawn_interval,
              1 if lair.guardians_spawned else 0))

    conn.commit()
    conn.close()
    print("Игра сохранена!")


def load_game_state():
    """ Загружает состояние. Возвращает словарь с данными или None """
    if not os.path.exists(DB_NAME):
        return None

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Сид
    cursor.execute('SELECT map_seed FROM game_state LIMIT 1')
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    seed = row[0]

    # Сущности
    cursor.execute('SELECT role, x, y, stats_json, effects_json, abilities_json, is_guardian, image_path FROM entities')
    entities_data = []
    for r in cursor.fetchall():
        entities_data.append({
            'role': r[0], 'x': r[1], 'y': r[2],
            'stats': json.loads(r[3]),
            'effects': json.loads(r[4]),
            'abilities': json.loads(r[5]),
            'is_guardian': bool(r[6]),
            'image_path': r[7]
        })

    # Логова
    cursor.execute('SELECT x, y, guardians_needed, next_spawn_interval, guardians_spawned FROM lairs')
    lairs_data = []
    for r in cursor.fetchall():
        lairs_data.append({
            'x': r[0], 'y': r[1],
            'guardians_needed': r[2],
            'next_spawn_interval': r[3],
            'guardians_spawned': bool(r[4])
        })

    conn.close()
    return {'seed': seed, 'entities': entities_data, 'lairs': lairs_data}