import random
from Entities.GameObject import GameObject
from Entities.Boss import Boss
from Shared.utils import load_json, get_image
from Shared.constants import*

# Stage (Total arena)
# Arena (Current stage)
class StageManager:
    def __init__(self, stages_data):
        self.finished = False

        self.stages_data = stages_data
        self.total_stage = len(stages_data)
        self.stage_counter = 1
        self.bg = None
        self.plat_list = []
        self.boss_list = []
        self.bullet_list = []

    def load_stage(self):
        self.boss_list.clear()
        cur_stage = self.stages_data[str(self.stage_counter)]

        bg = "background/" + cur_stage['bg']
        self.bg = get_image(bg, size_offsetx=WIDTH, size_offsety=HEIGHT)

        main_plat_img = "platform/" + cur_stage['main_plat_img']
        MainPlatform = GameObject(WIDTH//2, HEIGHT, WIDTH, 250, size_offsetx=200, image_path=main_plat_img,
                                                                size_offsety=1000)

        MainPlatform.rect.top = GROUND_Y

        self.plat_list = [MainPlatform]
        plat_img = cur_stage['plat_img']
        for xy in cur_stage['platforms']:
            self.add_plat(xy, plat_img)

        if 'random' in cur_stage['bosses']: 
            self.boss_list.append(self.generate_random_boss())
        else: 
            bosses_name = cur_stage['bosses'] # get boss names
            for b in bosses_name:
                boss_data = load_json(f"bosses/{b}.json")
                new_boss = Boss(b, boss_data, random.uniform(100, WIDTH - 100), random.choice([1 , -1]))
                self.boss_list.append(new_boss)

        
    def change_stage(self):
        self.stage_counter += 1
        if self.stage_counter > self.total_stage:
            self.finished = True
            print("you win")
            return
        else:
            print(f"Next stage\n Stage {self.stage_counter}")
            self.load_stage()

    def add_plat(self, coordinate, image="platform.png"):
        plat_size_offsetx=65
        plat_size_offsety=250
        image = "platform/" + image
        self.plat_list.append(GameObject(coordinate[0] , (GROUND_Y - coordinate[1]), 500, image_path=image, 
                                         size_offsetx=plat_size_offsetx, size_offsety=plat_size_offsety))
    
    def generate_boss_phase(self, num_phases=None): # generate boss stat randomly
        if num_phases is None:
            num_phases = random.randint(2, 5)  # random amount of phases

        boss_phase = {}

        patterns = ['circle', 'chaos', 'random', 'fan']
        images = ['bullet-1', 'bullet-2', 'bullet-3', 'bullet-orb']
        colors = [ORANGE, PURPLE, BLUE, CYAN, GOLD]
        max_bullet = 7
        max_rate = 1.0
        for phase in range(1, num_phases + 1):
            boss_phase[phase] = {
                'max_hp': random.randint(10, 25),
                'move_speed': random.randint(100, 700),
                'y_axis': random.randint(150, 600),
                'rate': random.uniform(0.2, max_rate),
                'pattern': random.choice(patterns),

                'num_bullet': random.randint(3, max_bullet),
                'bullet_spd': random.randint(200, 500),
                'bullet_size': random.randint(5, 12),

                'color': random.choice(colors),
                'image': random.choice(images)
            }
            colors.remove(boss_phase[phase]['color'])

        return boss_phase

    def generate_random_boss(self):
        size = random.randint(100, 200)
        start_x = random.uniform(100, WIDTH - 100)
        direction=random.choice([1 , -1])
        boss = Boss(f"Random boss", self.generate_boss_phase(), size, start_x, direction)
        return boss
