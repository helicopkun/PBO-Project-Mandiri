import pygame, random

from Shared.constants import*
from Shared.utils import load_json, get_image, circle_collide

from Entities.GameObject import GameObject
from Entities.Boss import Boss
from Entities.BossFactory import generate_boss_data, generate_random_boss

from Systems.ui import get_font

# Stage (Total arena)
# Arena (Current stage)
class StageManager:
    def __init__(self, stages_data):
        self.cleared = False
        self.clear_timestamp = 0
        self.win = False
        self.lost = False
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

        for p in self.particles[:]: #safely remove with copying list
            p.update(dt)
            if p.lifetime <= 0:
                self.particles.remove(p)

        if all(not b.alive for b in self.boss_list):
            if not self.cleared: #one time call
                self.clear_timestamp = pygame.time.get_ticks()
                self.bullet_list.clear()
            self.cleared = True
            return

        for b in self.boss_list:
            b.update(dt, player, self.bullet_list)

            for atk in player.active_attacks:
                for hitbox in atk['active_hitboxes']:
                    if hitbox.colliderect(b.rect):
                        player.attacked(b, atk, self.particles)   
                    
        for bullet in self.bullet_list[:]: #safely remove with copying list
            bullet.update(dt)

            if bullet.out_of_bounds():
                self.bullet_list.remove(bullet)
                continue
            
            #Check i-frame & kolisi player
            if circle_collide(player.rect.center, player.cur_hitbox, bullet.rect.center, bullet.hitbox_radius):
                # Absorb
                if player.absorb_active and not player.is_phasing: 
                    player.absorbed(bullet, self.particles)
                    self.bullet_list.remove(bullet)
                    continue
                
                # Got hit
                if not player.is_phasing and not player.grace_active: #grace_active = grace active or not
                    player.take_damage(self.particles)
                    self.bullet_list.remove(bullet)
                    continue

    def draw_stage(self, surface):
        bg_rect = surface.get_rect()
        surface.blit(self.bg, bg_rect)

        for platform in self.plat_list:
            platform.draw_self(surface)
        
    def draw_entities(self, surface):
        for bullet in self.bullet_list:
            bullet.draw_self(surface)
            if show_bullet_hitbox: bullet.draw_hitcircle(surface, YELLOW)

        for b in self.boss_list:
            b.draw(surface)
        
        for p in self.particles:
            p.draw(surface)

    def load_stage(self, surface, player):
        self._reset_entities(player)

        cur_stage = self.stages_data[str(self.stage_counter)]
 
        bg = "background/" + cur_stage['bg']
        self.bg = get_image(bg, size_offsetx=BG_WIDTH, size_offsety=BG_HEIGHT)

        main_plat_img = "platform/" + cur_stage['main_plat_img']
        MainPlatform = GameObject(0, 0, BG_WIDTH-BG_BORDER_X*2, 250, size_offsetx=200, image_path=main_plat_img,
                                                           size_offsety=1000)
        MainPlatform.rect.centerx = BG_WIDTH//2
        MainPlatform.rect.top = GROUND_Y

        self.plat_list = [MainPlatform]
        plat_img = cur_stage['plat_img']
        for xy in cur_stage['platforms']:
            self._add_plat(xy, plat_img)

        for b in cur_stage['bosses']:
            if b == 'random': 
                self.boss_list.append(generate_random_boss())
            else:
                boss_data = load_json(f"bosses/{b}.json")
                new_boss = Boss(b, boss_data, random.uniform(BG_BORDER_X + 1000, BG_WIDTH - BG_BORDER_X), random.choice([1 , -1]))
                self.boss_list.append(new_boss)

        self._stage_transition(surface)
        
    def change_stage(self, surface, player):
        self.cleared = False
        self.clear_timestamp = 0
        self.stage_counter += 1
        if self.stage_counter <= self.total_stage:
            self.load_stage(surface, player)
        else: 
            self.win = True

    def retry(self, surface, player):
        self.win = False
        self.lost = False
        player.is_dead = False
        self.stage_counter = 1
        self.load_stage(surface, player)


    def _stage_transition(self, surface): #surface surface
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

    def _reset_entities(self, player):
        self.particles.clear()
        self.bullet_list.clear()
        self.boss_list.clear()
        player.active_attacks.clear()
        player.phase_bar = player.config['phase_max']
        player.stamina_bar = player.config['stamina_max']
        player.hp = player.max_hp
        player.rect.left = BG_BORDER_X + 10
        player.rect.bottom = GROUND_Y
        
    def _add_plat(self, coordinate, image="platform.png"):
        plat_size_offsetx=65
        plat_size_offsety=250
        image = "platform/" + image
        self.plat_list.append(GameObject(BG_BORDER_X + coordinate[0] + 80 , (GROUND_Y - coordinate[1]), 300, image_path=image, 
                                         size_offsetx=plat_size_offsetx, size_offsety=plat_size_offsety))
