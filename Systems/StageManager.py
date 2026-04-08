import pygame, random

from Shared.constants import*
from Shared.utils import load_json, get_image, circle_collide

from Entities.GameObject import GameObject
from Entities.Boss import Boss
from Entities.Particle import Particle

from Systems.ui import get_font

# Stage (Total arena)
# Arena (Current stage)
class StageManager:
    def __init__(self, stages_data):
        self.win = False
        self.lost = False
        self.transitioning = False
        self.stages_data = stages_data
        self.total_stage = len(stages_data)
        self.stage_counter = 1
        self.bg = None
        self.plat_list = []
        self.boss_list = []
        self.bullet_list = []
        self.particles = []

    def update_entities(self, dt, player):
        if player.is_dead: 
            self.lost = True
            return
        
        for b in self.boss_list:
            if self.transitioning: break
            b.update(dt, player, self.bullet_list)


            for atk in player.active_attacks:
                for hitbox in atk['active_hitboxes']:
                    if hitbox.colliderect(b.rect):
                        player.attacked(b, atk, self.particles)

                for enemy in list(atk['target']): #reduce tick_rate cd 
                    if atk['target'][enemy] > 0:
                        atk['target'][enemy] -= dt    
                    
                        
        for p in self.particles[:]: #safely remove with copying list
            p.update(dt)
            if p.lifetime <= 0:
                self.particles.remove(p)
        
        for bullet in self.bullet_list[:]: #safely remove with copying list
            bullet.update(dt)

            if bullet.out_of_bounds():
                self.bullet_list.remove(bullet)
                return
            
            #Check i-frame & kolisi player
            if circle_collide(player.rect.center, player.cur_hitbox, bullet.rect.center, bullet.hitbox_radius):
                # Absorb
                if player.absorb_active and not player.is_phasing: 
                    player.absorbed(bullet, self.particles)
                    self.bullet_list.remove(bullet)
                    return
                
                # Got hit
                if not player.is_phasing and not player.grace_active: #grace_active = grace active or not
                    player.take_damage(self.particles)
                    self.bullet_list.remove(bullet)
                    return

    def draw_stage(self, surface):
        bg_rect = surface.get_rect()
        surface.blit(self.bg, bg_rect)

        for platform in self.plat_list:
            if show_hitbox: pygame.draw.rect(surface, BROWN, platform.rect) #hitbox
            platform.draw_self(surface)
        
    def draw_entities(self, surface):
        for bullet in self.bullet_list:
            bullet.draw_self(surface)
            if show_bullet_hitbox: bullet.draw_hitcircle(surface, RED)

        for b in self.boss_list:
            b.draw(surface)
            if show_hitbox: pygame.draw.rect(surface, RED, b.rect, 2) # boss hitbox
        
        for p in self.particles:
            p.draw(surface)

    def load_stage(self):
        self.boss_list.clear()
        cur_stage = self.stages_data[str(self.stage_counter)]
 
        bg = "background/" + cur_stage['bg']
        self.bg = get_image(bg, size_offsetx=BG_WIDTH, size_offsety=BG_HEIGHT)

        main_plat_img = "platform/" + cur_stage['main_plat_img']
        MainPlatform = GameObject(0, 0, SCREEN_WIDTH, 250, size_offsetx=200, image_path=main_plat_img,
                                                                size_offsety=1000)
        MainPlatform.rect.centerx = BG_WIDTH//2
        MainPlatform.rect.top = GROUND_Y

        self.plat_list = [MainPlatform]
        plat_img = cur_stage['plat_img']
        for xy in cur_stage['platforms']:
            self._add_plat(xy, plat_img)

        if 'random' in cur_stage['bosses']: 
            self.boss_list.append(self._generate_random_boss())
        else: 
            bosses_name = cur_stage['bosses'] # get boss names
            for b in bosses_name:
                boss_data = load_json(f"bosses/{b}.json")
                new_boss = Boss(b, boss_data, random.uniform(100, SCREEN_WIDTH - 100), random.choice([1 , -1]))
                self.boss_list.append(new_boss)

    def change_stage(self, surface, player):
        self.stage_counter += 1
        if self.stage_counter <= self.total_stage:
            self._reset_entities(player)
            self.load_stage()
            self._stage_transition(surface)
            self.transitioning = False
        else: 
            self.win = True
            
    def _stage_transition(self, surface): #surface surface
        self.transitioning = True
        font = get_font(72)
        text = font.render(f"Stage {self.stage_counter}", True, (255, 255, 255))
        text_rect = text.get_rect(center=(surface.get_width() // 2, surface.get_height() // 2))
        fade_surface = surface
        fade_surface.fill((0, 0, 0))

        # Fade out
        pygame.time.delay(50)
        for alpha in range(0, 255, 5):
            fade_surface.set_alpha(alpha)
            surface.blit(fade_surface, (0, 0))
            pygame.display.flip()
            pygame.time.delay(10)

        # Show stage text
        surface.fill((0, 0, 0))
        surface.blit(text, text_rect)
        pygame.display.flip()
        pygame.time.delay(1500)  # hold for 1.5 seconds

        # Fade in
        for alpha in range(255, 0, -5):
            fade_surface.set_alpha(alpha)
            surface.blit(fade_surface, (0, 0))
            pygame.display.flip()
            pygame.time.delay(10)

    def retry(self, player):
        self.win = False
        self.lost = False
        self._reset_entities(player)
        self.stage_counter = 1
        self.load_stage()

    def _reset_entities(self, player):
        self.particles.clear()
        self.bullet_list.clear()
        player.active_attacks.clear()
        player.rect.left = 10
        player.rect.bottom = GROUND_Y
        
    def _add_plat(self, coordinate, image="platform.png"):
        plat_size_offsetx=65
        plat_size_offsety=250
        image = "platform/" + image
        self.plat_list.append(GameObject(coordinate[0] , (GROUND_Y - coordinate[1]), 500, image_path=image, 
                                         size_offsetx=plat_size_offsetx, size_offsety=plat_size_offsety))
    
    def _generate_boss_phase(self, num_phases=None): # generate boss stat randomly
        if num_phases is None:
            num_phases = random.randint(2, 5)  # random amount of phases

        boss_phase = {}

        patterns = ['circle', 'chaos', 'random', 'fan']
        images = ['bullet-1', 'bullet-2', 'bullet-3', 'bullet-orb']
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
                'bullet_img': random.choice(images)
            }

        return boss_phase

    def _generate_random_boss(self):
        start_x = random.uniform(100, SCREEN_WIDTH - 100)
        direction=random.choice([1 , -1])
        boss = Boss(f"Random boss", self._generate_boss_phase(), start_x, direction)
        return boss

