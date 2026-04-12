import random

from Entities.Boss import Boss
from Shared.constants import BG_WIDTH, BG_BORDER_X


def generate_boss_data(num_phases=None): # generate boss stat randomly
    if num_phases is None:
        num_phases = random.randint(2, 5)  # random amount of phases
    movement = ['bop', 'box', 'chase', 'random', 'middle']
    img = ['enemy.png']
    size = random.randint(100, 250)
    color = [random.randint(100, 250),
                random.randint(100, 250),
                random.randint(100, 250)]
    boss_data = {}
    boss_data['boss_img'] = random.choice(img)
    boss_data['size'] = size
    boss_data['color'] = color
    boss_phase = {}
    patterns = ['circle', 'chaos', 'random', 'fan', 'spiral', 'burst', 'cross', 'aimed']
    images = ['bullet-1', 'bullet-2', 'bullet-3', 'bullet-orb']
    max_bullet = 7
    max_rate = 1.0
    for phase in range(1, num_phases + 1):
        boss_phase[str(phase)] = {
            'max_hp': random.randint(10, 25),
            'movement': random.choice(movement),
            'move_speed': random.randint(100, 700),
            'y_axis': random.randint(150, 600),
            'rate': random.uniform(0.2, max_rate),
            'pattern': random.choice(patterns),

            'num_bullet': random.randint(3, max_bullet),
            'bullet_spd': random.randint(200, 500),
            'bullet_size': random.randint(5, 12),
            'bullet_img': random.choice(images)
        }
    boss_data['phase'] = boss_phase

    return boss_data

def generate_random_boss():
    start_x = random.uniform(BG_WIDTH//2, BG_WIDTH - BG_BORDER_X)
    direction=random.choice([1 , -1])
    boss = Boss(f"Random boss", generate_boss_data(), start_x, direction)
    return boss

