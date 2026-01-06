from collections import deque
import random
from constants import *


def apply_ability(source, target, effect):
    effect_script = effect
    s_data = source.get_as_dict()
    t_data = target.get_as_dict()
    pending_buffs = []

    def buff_func(target_dict, stat, val, dur):
        target_obj = None
        if target_dict.get('role') == source.role:
            target_obj = source
        elif target_dict.get('role') == target.role:
            target_obj = target
        if target_obj:
            pending_buffs.append((target_obj, stat, val, dur))

    context = {'hero': s_data, 'target': t_data, 'd4': random.randint(1, 4), 'buff': buff_func}
    try:
        for cmd in effect_script.split(';'):
            if cmd.strip(): exec(cmd.strip(), {}, context)
    except:
        pass

    for key in target.stats_dict.keys():
        target.stats_dict[key] = context['target'][key] - target.get_stat(key)[1]
    for key in source.stats_dict.keys():
        source.stats_dict[key] = context['hero'][key] - source.get_stat(key)[1]

    for (obj, stat, val, dur) in pending_buffs:
        obj.add_effect(stat, val, dur)


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
                # Проверка препятствий (можно добавить проверку типов тайлов города для врагов)
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
