import pygame
import sys
import random
import math

pygame.init()
pygame.font.init()

WIDTH = 1600
HEIGHT = 900

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dodge / Parry This: Boss Rush")

# UI Font
UI_FONT = pygame.font.SysFont("Impact", 32)

# Colors
CYAN = (0, 255, 255)
BLUE = (0, 0, 255)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
GOLD = (255, 215, 0)
PURPLE = (148, 0, 211)
ORANGE = (255, 165, 0)

class GameObject:
    def __init__ (self, x, y, width = 20, height = 20, hitbox_radius = 10):
        self.hitbox_radius = hitbox_radius
        self.width = width
        self.height = height
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.rect.center = (x, y)
    
    def draw_Hitbox(self, surface, color = WHITE):
        pygame.draw.circle(surface, color, self.rect.center, self.hitbox_radius) 

MainPlatform = GameObject(WIDTH//2, HEIGHT, WIDTH, HEIGHT - 300)

class Particle:
    def __init__(self, x, y, color=GOLD, is_burst=False):
        self.x = x
        self.y = y
        self.color = color
        self.size = random.uniform(4, 8)
        self.lifetime = random.uniform(0.2, 0.5)
        self.max_lifetime = self.lifetime
        
        # If it's a boss death burst, make them shoot out faster in a perfect circle
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(150, 400) if is_burst else random.uniform(50, 150)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.lifetime -= dt

    def draw(self, surface):
        if self.lifetime > 0:
            # Shrink as it fades
            current_size = max(0.1, self.size * (self.lifetime / self.max_lifetime))
            pygame.draw.rect(surface, self.color, (self.x, self.y, current_size, current_size))

class Player(GameObject):
    def __init__(self, sizeHitbox = 10):
        super().__init__(x= WIDTH//2, y=MainPlatform.rect.top - 50, width=25, height=25, hitbox_radius=sizeHitbox)
        self.sizeHitbox = sizeHitbox
        self.speedX = 400
        self.speedY = 400
        self.gravity = 250

        # Stats
        self.max_hp = 5
        self.hp = self.max_hp
        self.parry_count = 0 

        # I-Frames
        self.player_hit = False
        self.hit_time = 0
        self.hit_grace = 2200

        # Flight
        self.is_flying = False
        self.fly_barMax = 2 
        self.fly_barRate = 0.5 
        self.fly_barCD = 0.6 
        self.fly_barCD_time = 0
        self.fly_bar = 0 

        # Jump
        self.is_jumping = False 
        self.jump_delay = 0                          
        self.max_jump_delay = 0.15 
        self.jump_time = 0
        self.max_jump_time = 0.4 
        self.air_time = 0
        self.air_delay = 0.1 
        self.current_platform = MainPlatform
        self.platform_group = None
        
        # Parry
        self.is_parrying = False
        self.parry_key_pressed = False
        self.parry_duration = 0.3  
        self.parry_timer = 0
        self.parry_cd = 1  
        self.parry_cd_timer = 0
        self.parry_radius = 15
        self.parry_color = GOLD
        
        # Attack
        self.facing_right = True # Used to determine attack direction
        self.attack_cd = 5.0
        self.attack_cd_timer = 0
        self.is_attacking = False
        self.attack_duration = 0.15 # How long the attack hitbox stays out
        self.attack_timer = 0
        self.attack_rect = pygame.Rect(0,0,0,0)

    def update(self, keys, dt, platforms, boss):
        self.platform_group = platforms

        # Hit Grace       
        if self.player_hit and pygame.time.get_ticks() - self.hit_time >= self.hit_grace:
            self.player_hit = False
        
        # Parry Logic
        if (keys[pygame.K_k] or keys[pygame.MOUSEBUTTONDOWN]) and not (self.player_hit or self.is_flying):
            if not self.parry_key_pressed and not self.is_parrying and self.parry_cd_timer <= 0:
                self.is_parrying = True
                self.parry_timer = self.parry_duration
                self.parry_cd_timer = self.parry_cd
                self.parry_key_pressed = True
        else:
            self.parry_key_pressed = False

        if self.is_parrying:
            self.parry_timer -= dt
            if self.parry_timer <= 0: self.is_parrying = False
        if self.parry_cd_timer > 0: self.parry_cd_timer -= dt

        # Attack Logic (J key)
        if self.attack_cd_timer > 0: self.attack_cd_timer -= dt
        if self.is_attacking:
            self.attack_timer -= dt
            if self.attack_timer <= 0: self.is_attacking = False

        if keys[pygame.K_j] and self.attack_cd_timer <= 0 and not self.is_flying:
            self.is_attacking = True
            self.attack_timer = self.attack_duration
            self.attack_cd_timer = self.attack_cd
            
            # Create Attack Rect based on facing direction
            att_width = self.width * 2
            att_height = self.height * 2
            
            if self.facing_right:
                ax = self.rect.right
            else:
                ax = self.rect.left - att_width
            ay = self.rect.centery - (att_height / 2)
            
            self.attack_rect = pygame.Rect(ax, ay, att_width, att_height)
            
            # Check collision with boss instantly
            if boss and boss.hp > 0 and self.attack_rect.colliderect(boss.rect):
                boss.take_damage()

        # Update position for attack rect if active
        if self.is_attacking:
            if self.facing_right: self.attack_rect.left = self.rect.right
            else: self.attack_rect.right = self.rect.left
            self.attack_rect.centery = self.rect.centery

        # Movement
        self.move(keys, dt)
        if self.is_flying: self.hitbox_radius = 0
        else:              self.hitbox_radius = self.sizeHitbox

        # Flying bar update
        self.fly_bar_rectMax = pygame.Rect(0, 0, self.fly_barMax * 50, 10)
        self.fly_bar_rectMax.centerx = self.rect.centerx
        self.fly_bar_rectMax.centery = self.rect.bottom + 10
        self.fly_bar_rect = pygame.Rect(self.fly_bar_rectMax.left, self.fly_bar_rectMax.top, self.fly_bar * 50, 10)
            
    def draw(self, surface):
        if self.player_hit: player_color = RED     
        else: player_color = WHITE
        if self.is_flying: player_color = BLUE
        
        # Blinking I-frames
        if not (self.player_hit and pygame.time.get_ticks() % 200 < 100): 
            self.draw_Hitbox(surface, player_color)
        pygame.draw.rect(surface, player_color, self.rect, 2)

        # Draw Parry Radius
        if self.is_parrying:
            pygame.draw.circle(surface, self.parry_color, self.rect.center, self.hitbox_radius + self.parry_radius, 3)

        # Draw Attack Hitbox
        if self.is_attacking:
            pygame.draw.rect(surface, RED, self.attack_rect, 2)

        # Draw Fly Bar
        if self.fly_bar < self.fly_barMax:
            pygame.draw.rect(surface, BLUE, self.fly_bar_rect)
            pygame.draw.rect(surface, CYAN, self.fly_bar_rectMax, 2)

    def on_platform(self):
        for platform in self.platform_group:
            if self.rect.right > platform.rect.left and self.rect.left < platform.rect.right:
                if (self.rect.bottom >= platform.rect.top and self.rect.bottom <= platform.rect.top + platform.height / 2):
                    self.current_platform = platform
                    return True
        return False
    
    def move(self, keys, dt):
        # Determine facing direction for attack
        if keys[pygame.K_a]: self.facing_right = False
        if keys[pygame.K_d]: self.facing_right = True

        #Flying movement
        if keys[pygame.K_LSHIFT]:
            if self.fly_bar > 0:
                self.fly_bar -= dt
                self.hitbox_radius = 0
                self.is_flying = True 
            else:
                self.hitbox_radius = self.sizeHitbox
                self.is_flying = False
            self.fly_barCD_time = pygame.time.get_ticks() / 1000 
        else:
            curCD_time = pygame.time.get_ticks() / 1000
            if curCD_time - self.fly_barCD_time >= self.fly_barCD: 
                self.fly_bar = min(self.fly_barMax, self.fly_bar + self.fly_barRate * dt)
            self.hitbox_radius = self.sizeHitbox
            self.is_flying = False

        if self.is_flying:
            dx = 0; dy = 0
            if keys[pygame.K_a]: dx = -1
            if keys[pygame.K_d]: dx = 1
            if keys[pygame.K_w]: dy = -1
            if keys[pygame.K_s]: dy = 1

            if dx != 0 and dy != 0:
                length = (dx**2 + dy**2) ** 0.5
                dx /= length
                dy /= length
        
            if self.rect.left > 0 and self.rect.right < WIDTH: self.rect.centerx += dx * self.speedX * dt
            if self.rect.top > 0 and self.rect.bottom <= MainPlatform.rect.top: self.rect.centery += dy * self.speedY * dt
            
            if self.rect.left < 0 : self.rect.left = 0 
            if self.rect.right > WIDTH : self.rect.right = WIDTH 
            if self.rect.top < 0 : self.rect.top = 0 
            if self.rect.bottom > MainPlatform.rect.top: self.rect.bottom = MainPlatform.rect.top
            return 

        #Horizontal movement
        if keys[pygame.K_a] and self.rect.left > 0:
                self.rect.centerx -= self.speedX * dt
                self.rect.left = max(0, self.rect.left)

        if keys[pygame.K_d] and self.rect.right < WIDTH:
                self.rect.centerx += self.speedX * dt
                self.rect.right = min(WIDTH, self.rect.right)

        #Vertical movement
        if keys[pygame.K_s] and not self.rect.bottom >= MainPlatform.rect.top:
            self.rect.centery += self.speedY * dt
        if (keys[pygame.K_w] or keys[pygame.K_SPACE]) and (not keys[pygame.K_s] and self.on_platform() and not self.is_jumping):
            if self.jump_delay >= self.max_jump_delay:
                self.is_jumping = True                  
                self.jump_time = 0
                self.jump_delay = 0
        
        if self.is_jumping:
            if (keys[pygame.K_w] or keys[pygame.K_SPACE]) and (not keys[pygame.K_s] and self.rect.top > 0):
                if self.jump_time < self.max_jump_time:                           
                    self.rect.centery -= self.speedY * dt
                    self.jump_time += dt
                else: self.is_jumping = False
            else: self.is_jumping = False

        if self.on_platform() and not self.is_jumping and not keys[pygame.K_s]:
            self.jump_delay += dt
            self.air_time = 0
            if self.current_platform is MainPlatform:
                self.rect.bottom = MainPlatform.rect.top
                 
        if not self.on_platform() and not self.is_jumping:
            self.air_time += dt
            if self.air_time > self.air_delay: self.rect.centery += self.gravity * dt


class Bullet(GameObject):
    def __init__(self, x, y, vx, vy, color=CYAN):
        super().__init__(x, y, hitbox_radius=8)
        self.vx = vx
        self.vy = vy
        self.color = color

    def update(self, dt):
        self.rect.centerx += self.vx * dt
        self.rect.centery += self.vy * dt
        
    def out_of_bounds(self):
        return self.rect.right < -50 or self.rect.left > WIDTH + 50 or self.rect.top > HEIGHT or self.rect.bottom < -50


class Boss(GameObject):
    def __init__(self):
        super().__init__(x=WIDTH//2, y=150, width=60, height=60, hitbox_radius=30)
        self.total_phases = 5
        self.current_phase = 1
        self.max_hp = 5
        self.hp = self.max_hp
        self.active = True
        
        self.direction = 1 # 1 for right, -1 for left
        self.fire_timer = 0
        
        # Define Phase Data: Speed, Fire Rate, Bullet Speed, Pattern
        self.phases = {
            1: {'move_speed': 100, 'rate': 1.5, 'pattern': 'fan_3', 'bullet_spd': 300, 'color': ORANGE},
            2: {'move_speed': 200, 'rate': 1.2, 'pattern': 'fan_5', 'bullet_spd': 350, 'color': PURPLE},
            3: {'move_speed': 300, 'rate': 1.0, 'pattern': 'circle_8', 'bullet_spd': 200, 'color': RED},
            4: {'move_speed': 450, 'rate': 0.8, 'pattern': 'fan_7', 'bullet_spd': 400, 'color': CYAN},
            5: {'move_speed': 550, 'rate': 0.4, 'pattern': 'chaos', 'bullet_spd': 450, 'color': WHITE}
        }
        
    def update(self, dt, player, enemy_list):
        if not self.active: return
        
        phase = self.phases[self.current_phase]
        
        # Movement Flight Loop (Left/Right)
        self.rect.x += phase['move_speed'] * self.direction * dt
        if self.rect.right > WIDTH - 100:
            self.direction = -1
        elif self.rect.left < 100:
            self.direction = 1
            
        # Shooting logic
        self.fire_timer -= dt
        if self.fire_timer <= 0:
            self.fire_timer = phase['rate']
            self.shoot(player, enemy_list, phase)
            
    def shoot(self, player, enemy_list, phase_data):
        pattern = phase_data['pattern']
        spd = phase_data['bullet_spd']
        color = phase_data['color']
        cx, cy = self.rect.center
        
        if pattern.startswith('fan'):
            num_bullets = int(pattern.split('_')[1]) # Extract number (e.g., 3, 5, 7)
            angle_to_player = math.atan2(player.rect.centery - cy, player.rect.centerx - cx)
            spread = math.radians(20) # 20 degrees between each bullet
            
            # Start angle so that the middle bullet aims exactly at the player
            start_angle = angle_to_player - (spread * (num_bullets // 2))
            
            for i in range(num_bullets):
                a = start_angle + (spread * i)
                bx = math.cos(a) * spd
                by = math.sin(a) * spd
                enemy_list.append(Bullet(cx, cy, bx, by, color))
                
        elif pattern.startswith('circle'):
            num_bullets = int(pattern.split('_')[1])
            step = (math.pi * 2) / num_bullets
            for i in range(num_bullets):
                a = step * i
                bx = math.cos(a) * spd
                by = math.sin(a) * spd
                enemy_list.append(Bullet(cx, cy, bx, by, color))
                
        elif pattern == 'chaos':
            for _ in range(3):
                a = random.uniform(0, math.pi * 2)
                bx = math.cos(a) * spd
                by = math.sin(a) * spd
                enemy_list.append(Bullet(cx, cy, bx, by, color))
                
    def take_damage(self):
        self.hp -= 1
        spawn_particles(self.rect.centerx, self.rect.centery, color=RED, count=10) # Hit feedback
        if self.hp <= 0:
            self.advance_phase()
            
    def advance_phase(self):
        # Trigger massive death particle burst
        spawn_particles(self.rect.centerx, self.rect.centery, color=GOLD, count=30, is_burst=True)
        
        self.current_phase += 1
        if self.current_phase > self.total_phases:
            self.active = False # Boss defeated!
        else:
            self.hp = self.max_hp

    def draw(self, surface):
        if not self.active: return
        color = self.phases[self.current_phase]['color']
        self.draw_Hitbox(surface, color)
        pygame.draw.rect(surface, color, self.rect, 2)


def circle_collide(c1_pos, r1, c2_pos, r2):
    dx = c1_pos[0] - c2_pos[0] 
    dy = c1_pos[1] - c2_pos[1]
    return dx*dx + dy*dy <= (r1 + r2) ** 2

# Global Particle Manager
particles = []
def spawn_particles(x, y, color, count=5, is_burst=False):
    for _ in range(count):
        particles.append(Particle(x, y, color, is_burst))

def draw_ui(surface, player, boss):
    # Player UI
    p_text = UI_FONT.render("PLAYER", True, WHITE)
    surface.blit(p_text, (20, 20))
    # HP Bar
    pygame.draw.rect(surface, RED, (20, 60, player.max_hp * 40, 20))
    pygame.draw.rect(surface, GREEN, (20, 60, player.hp * 40, 20))
    pygame.draw.rect(surface, WHITE, (20, 60, player.max_hp * 40, 20), 2)
    
    # Parry/Heal tracking
    parry_txt = UI_FONT.render(f"Parry Stack: {player.parry_count}/5", True, GOLD)
    surface.blit(parry_txt, (20, 90))
    
    # Boss UI
    if boss.active:
        b_name = UI_FONT.render(f"THE POLYGON (Phase {boss.current_phase}/{boss.total_phases})", True, WHITE)
        name_rect = b_name.get_rect(topright=(WIDTH - 20, 20))
        surface.blit(b_name, name_rect)
        
        bar_width = boss.max_hp * 60
        bar_x = WIDTH - 20 - bar_width
        pygame.draw.rect(surface, RED, (bar_x, 60, bar_width, 20))
        pygame.draw.rect(surface, boss.phases[boss.current_phase]['color'], (bar_x, 60, boss.hp * 60, 20))
        pygame.draw.rect(surface, WHITE, (bar_x, 60, bar_width, 20), 2)
    else:
        win_txt = UI_FONT.render("BOSS DEFEATED!", True, GOLD)
        win_rect = win_txt.get_rect(topright=(WIDTH - 20, 20))
        surface.blit(win_txt, win_rect)

# ----------------- MAIN LOOP SETUP ----------------- #

Platforms = [MainPlatform]
Platforms.append(GameObject(400, HEIGHT//2, 200, 10))
Platforms.append(GameObject(900, HEIGHT//2, 200, 15))

tes = Player(sizeHitbox=5)
boss = Boss()
enemies = [] 

# Screen Shake Variables
shake_timer = 0
world_surface = pygame.Surface((WIDTH, HEIGHT))

clock = pygame.time.Clock()
running = True

while running:
    dt = clock.tick(60) / 1000 
    keys = pygame.key.get_pressed()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
    # Update Entities
    tes.update(keys, dt, Platforms, boss)
    boss.update(dt, tes, enemies)
    
    for p in particles[:]:
        p.update(dt)
        if p.lifetime <= 0:
            particles.remove(p)

    for enemy in enemies[:]:
        enemy.update(dt)
        
        # Despawn if out of bounds
        if enemy.out_of_bounds():
            enemies.remove(enemy)
            continue
            
        # Check Parry & Collision
        current_radius = tes.hitbox_radius + (tes.parry_radius if tes.is_parrying else 0) 
        if circle_collide(tes.rect.center, current_radius, enemy.rect.center, enemy.hitbox_radius):
            
            if tes.is_parrying and not tes.is_flying:
                # SUCCESSFUL PARRY
                enemies.remove(enemy)
                tes.fly_bar = min(tes.fly_barMax, tes.fly_bar + 0.5)
                spawn_particles(enemy.rect.centerx, enemy.rect.centery, GOLD, 6) # Parry Sparks
                
                tes.parry_count += 1
                if tes.parry_count >= 5:
                    tes.hp = min(tes.hp + 1, tes.max_hp)
                    tes.parry_count = 0
                    spawn_particles(tes.rect.centerx, tes.rect.centery, GREEN, 15) # Heal Sparks
                continue
            
            if not tes.is_flying and not tes.player_hit:
                # HIT BY BULLET
                enemies.remove(enemy)
                tes.hp -= 1
                tes.hit_time = pygame.time.get_ticks()
                tes.player_hit = True
                shake_timer = 0.25 # Trigger Screen Shake
                spawn_particles(tes.rect.centerx, tes.rect.centery, RED, 10)
                
                if tes.hp <= 0:
                    print("GAME OVER")
                    running = False # Very simple game over for now
                continue

    # Update Screen Shake Timeraj
    if shake_timer > 0:
        shake_timer -= dt

    # ---------------- DRAWING ---------------- #
    # Draw everything to world_surface first (so we can shake it)
    world_surface.fill(BLACK)
    
    for platform in Platforms:
        pygame.draw.rect(world_surface, GREEN, platform.rect)
    
    boss.draw(world_surface)
    tes.draw(world_surface)
    
    for enemy in enemies:
        enemy.draw_Hitbox(world_surface, enemy.color)
        
    for p in particles:
        p.draw(world_surface)

    # Apply Screen Shake to final render
    shake_x, shake_y = 0, 0
    if shake_timer > 0:
        shake_intensity = 8
        shake_x = random.randint(-shake_intensity, shake_intensity)
        shake_y = random.randint(-shake_intensity, shake_intensity)
        
    screen.blit(world_surface, (shake_x, shake_y))
    
    # Draw UI on top of everything (we don't want the UI to shake)
    draw_ui(screen, tes, boss)

    pygame.display.update()

pygame.quit()
sys.exit()