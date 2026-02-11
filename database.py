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
            map_seed INTEGER,
            name TEXT,
            time_of_creation TEXT,
            coins INTEGER,
            reputation INTEGER,
            quest  TEXT
        )
    ''')

    # Таблица сущностей (Герои и Враги)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            role TEXT,
            x REAL,
            y REAL,
            stats_json TEXT,
            effects_json TEXT,
            abilities_json TEXT,
            is_guardian INTEGER,
            is_boss INTEGER,
            image_path TEXT,
            map_id INTEGER,
            FOREIGN KEY (map_id) REFERENCES game_state (id) ON DELETE CASCADE
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
            guardians_spawned INTEGER,
            map_id INTEGER,
            FOREIGN KEY (map_id) REFERENCES game_state (id) ON DELETE CASCADE
        )
    ''')

    # Справочник предметов (Items)
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                image_path TEXT,
                price INTEGER,
                stats_json TEXT,
                abilities_json TEXT
            )
        ''')

    # Инвентарь (Связь сущностей и предметов)
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                FOREIGN KEY (entity_id) REFERENCES entities (id) ON DELETE CASCADE,
                FOREIGN KEY (item_id) REFERENCES items (id) ON DELETE CASCADE
            )
        ''')

    conn.commit()
    conn.close()

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")  # Включаем поддержку связей
    return conn


def save_game_state(world, heroes, enemies, lairs):
    conn = get_connection()
    cursor = conn.cursor()

    name = world.get('name')
    time_created = world.get('time_of_creation')

    # Ищем, есть ли уже такое сохранение
    cursor.execute('SELECT id FROM game_state WHERE name = ? AND time_of_creation = ?',
                   (name, time_created))
    row = cursor.fetchone()

    if row:
        save_id = row[0]
        # Очищаем старые данные сущностей и логов для этого ID
        cursor.execute('DELETE FROM entities WHERE map_id = ?', (save_id,))
        cursor.execute('DELETE FROM lairs WHERE map_id = ?', (save_id,))
        cursor.execute('DELETE FROM inventory WHERE map_id = ?', (save_id,))
        # Обновляем сид (на всякий случай)
        cursor.execute('UPDATE game_state SET map_seed = ? WHERE id = ?', (world.get('seed'), save_id))
    else:
        # Создаем новую запись
        cursor.execute('''INSERT INTO game_state (map_seed, name, time_of_creation,
         coins, reputation, quest) VALUES (?, ?, ?, ?, ?, ?)''',
                       (world.get('seed'), name, time_created,
                        world.get('coins'), world.get('rep'), json.dumps(world.get('quest'))))
        save_id = cursor.lastrowid

    # Сохраняем сущности
    all_entities = [*heroes, *enemies]
    for entity in all_entities:
        cursor.execute('''
            INSERT INTO entities (name, role, x, y, stats_json, effects_json, abilities_json,
             is_guardian, is_boss, image_path, map_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (entity.name, entity.role, entity.center_x, entity.center_y,
              json.dumps(entity.stats_dict), json.dumps(entity.active_effects),
              json.dumps(entity.abilities), 1 if getattr(entity, 'is_guardian', False) else 0,
              1 if getattr(entity, 'is_boss', False) else 0, entity.image_path, save_id))
        entity_db_id = cursor.lastrowid
        for item in getattr(entity, 'inventory', []):
            # 1. Добавляем предмет в справочник, если его там нет (по имени)
            cursor.execute('''
                        INSERT OR IGNORE INTO items (name, image_path, price, stats_json, abilities_json)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (item.name, item.image_path, getattr(item, 'price', 0),
                          json.dumps(getattr(item, 'stats_dict', {})),
                          json.dumps(getattr(item, 'abilities', []))))

            # Получаем ID предмета
            cursor.execute('SELECT id FROM items WHERE name = ?', (item.name,))
            item_id = cursor.fetchone()[0]

            # 2. Создаем связь в таблице inventory
            cursor.execute('INSERT INTO inventory (entity_id, item_id) VALUES (?, ?)',
                           (entity_db_id, item_id))

    for lair in lairs:
        cursor.execute('''
            INSERT INTO lairs (x, y, guardians_needed, next_spawn_interval, guardians_spawned, map_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (lair.center_x, lair.center_y, lair.guardians_needed, lair.next_spawn_interval,
              1 if lair.guardians_spawned else 0, save_id))

    conn.commit()
    conn.close()
    print("Игра сохранена!")

def get_recent_saves(limit=5):
    """ Возвращает последние сохранения """
    if not os.path.exists(DB_NAME): return []
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, time_of_creation FROM game_state ORDER BY id DESC LIMIT ?',
                   (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def load_game_state(save_id):
    conn = get_connection()
    cursor = conn.cursor()
    world = dict()

    cursor.execute('SELECT map_seed, coins, reputation, quest FROM game_state WHERE id = ?', (save_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    world['seed'] = row[0]
    world['coins'] = row[1]
    world['rep'] = row[2]
    world['quest'] = json.loads(row[3])

    cursor.execute('''SELECT name, role, x, y, stats_json, effects_json, abilities_json,
     is_guardian, is_boss, image_path FROM entities WHERE map_id = ?''', (save_id,))
    entities_rows = cursor.fetchall()
    entities_data = []

    for r in entities_rows:
        entity_id = r[0]
        # Для каждой сущности тянем её предметы через JOIN
        cursor.execute('''
                SELECT i.name, i.image_path, i.price, i.stats_json, i.abilities_json
                FROM items i
                JOIN inventory inv ON i.id = inv.item_id
                WHERE inv.entity_id = ?
            ''', (entity_id,))

        items_data = [{
            'name': ir[0], 'image_path': ir[1], 'price': ir[2],
            'stats': json.loads(ir[3]), 'abilities': json.loads(ir[4])
        } for ir in cursor.fetchall()]
        entities_data.append({
            'name': r[0], 'role': r[1], 'x': r[2], 'y': r[3],
            'stats': json.loads(r[4]), 'effects': json.loads(r[5]),
            'abilities': json.loads(r[6]), 'is_guardian': bool(r[7]), 'is_boss': bool(r[8]),
            'image_path': r[9],
            'inventory': items_data  # Добавляем список предметов в данные сущности
        })

    cursor.execute('SELECT x, y, guardians_needed, next_spawn_interval, guardians_spawned FROM lairs WHERE map_id = ?', (save_id,))
    lairs_data = [{
        'x': r[0], 'y': r[1], 'guardians_needed': r[2],
        'next_spawn_interval': r[3], 'guardians_spawned': bool(r[4])
    } for r in cursor.fetchall()]

    conn.close()
    return {'world': world, 'entities': entities_data, 'lairs': lairs_data}