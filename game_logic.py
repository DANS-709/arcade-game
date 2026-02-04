from collections import deque
import random
from tkinter import filedialog  # для выбора файла
import tkinter as tk
from constants import *
import zipfile
import json


def apply_ability(source, target, effect, eff_manager=None):
    effect_script = effect
    s_data = source.get_as_dict()
    t_data = target.get_as_dict()
    pending_buffs = []
    source_old_hp = s_data['hp']
    target_old_hp = t_data['hp']

    def buff_func(targ, stat, val, dur):
        target_obj = None
        if targ.lower() == 'target':
            target_obj = target
        elif targ.lower() == 'hero':
            target_obj = source

        if target_obj:
            pending_buffs.append((target_obj, stat, val, dur))

    context = {'hero': s_data, 'target': t_data, 'd4': random.randint(1, 4), 'buff': buff_func}
    try:
        for cmd in effect_script.split(';'):
            if cmd.strip(): exec(cmd.strip(), {}, context)
    except Exception as e:
        print(f"Ошибка применения эффекта: {e}")
        source['moves_left'] += 1  # если произошла ошибка, то возвращаем ход
        return


    for key in target.stats_dict.keys():
        target.stats_dict[key] = context['target'][key] - target.get_stat(key)[1]
    for key in source.stats_dict.keys():
        source.stats_dict[key] = context['hero'][key] - source.get_stat(key)[1]

    for (obj, stat, val, dur) in pending_buffs:
        obj.add_effect(stat, val, dur)
    if eff_manager:
        source.start_attack_animation((target.center_x, target.center_y))
        if source.get_stat('hp')[0] < source_old_hp:  # Если HP уменьшилось
            eff_manager.add_damage_effect(source.center_x, source.center_y)
            target.start_shake()
        elif source.get_stat('hp')[0] > source_old_hp:  # HP увеличилось
            eff_manager.add_heal_effect(source.center_x, source.center_y)
        if target.get_stat('hp')[0] < target_old_hp:  # Если HP уменьшилось
            eff_manager.add_damage_effect(target.center_x, target.center_y)
            target.start_shake()
        elif target.get_stat('hp')[0] > target_old_hp:  # HP увеличилось
            eff_manager.add_heal_effect(target.center_x, target.center_y)



def bfs_path(start_grid, target_grid, grid_width=GRID_WIDTH, grid_height=GRID_HEIGHT, obstacles=None):
    """ Поиск кратчайшего пути (BFS) """
    queue = deque([start_grid])
    came_from = {start_grid: None}

    if obstacles is None:
        obstacles = set()

    while queue:
        current = queue.popleft()
        if current == target_grid:
            break

        cx, cy = current
        # Соседи (верх, низ, лево, право)
        neighbors = [(cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)]

        for next_node in neighbors:
            nx, ny = next_node
            # Проверка границ
            if 0 <= nx < grid_width and 0 <= ny < grid_height:
                # Проверка препятствий
                if next_node not in came_from and next_node not in obstacles:
                    queue.append(next_node)
                    came_from[next_node] = current

    # Восстановление пути
    if target_grid not in came_from:
        return []  # Путь не найден

    path = []
    curr = target_grid
    while curr != start_grid:
        path.append(curr)
        curr = came_from[curr]
    path.reverse()
    return path



def load_characters_from_zip():
    # Создаем окно для выбора файла
    root = tk.Tk()
    root.withdraw()  # Скрываем основное окно

    # Открываем диалоговое окно выбора файла
    file_path = filedialog.askopenfilename(
        filetypes=[("ZIP files", "*.zip")]
    )

    if not file_path:
        return []

    characters = []

    try:
        # Открываем выбранный zip-архив
        with zipfile.ZipFile(file_path, 'r') as zip_file:
            # Получаем список всех JSON-файлов в архиве
            json_files = [name for name in zip_file.namelist() if name.endswith('.json')]
            # Загружаем данные каждого персонажа
            for file_name in json_files[:4]:  # Ограничиваем количество героев
                with zip_file.open(file_name) as file:
                    data = json.load(file)
                    characters.append(data)

    except Exception as e:
        print(f"Ошибка при загрузке данных: {str(e)}")
        return []

    return characters