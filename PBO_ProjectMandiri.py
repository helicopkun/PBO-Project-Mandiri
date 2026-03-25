import pygame
import sys
import random

pygame.init()

WIDTH = 1600
HEIGHT = 900

screen = pygame.display.set_mode((WIDTH, HEIGHT))
   
pygame.display.set_caption("Dodge / parry this")

CYAN = (0, 255, 255)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

class GameObject: #Circle Hitbox
    def __init__ (self, x, y, width = 20, height = 20, hitbox_radius = 10):
        self.hitbox_radius = hitbox_radius
        self.width = width
        self.height = height
        self.rect = pygame.Rect(0, 0,
                                self.width, self.height)
        self.rect.center = (x, y)
    
    def draw_Hitbox(self, surface, color = WHITE): #draw hitbox circle
        pygame.draw.circle(surface, color,
                            self.rect.center, self.hitbox_radius) 


MainPlatform = GameObject(WIDTH//2, HEIGHT, WIDTH, HEIGHT - 300)
class Player(GameObject):
    def __init__(self, sizeHitbox = 5): #customize player, offset = character size
        super().__init__(x= 15, y=MainPlatform.rect.top, width=25, height=25, hitbox_radius=sizeHitbox)
        self.sizeHitbox = sizeHitbox
        self.speedX = 400
        self.speedY = 400
        self.gravity = 250

        self.player_hit = False # hit grace setelah kena hit
        self.hit_time = 0
        self.hit_grace = 2200

        self.is_flying = False
        self.fly_barMax = 2 #sekon
        self.fly_barRate = 0.5 #bar recharge per second
        self.fly_barCD = 0.6 #cooldown before recharge
        self.fly_barCD_time = 0
        self.fly_bar = 0 # current bar

        self.is_jumping = False 
        self.jump_delay = 0                          
        self.max_jump_delay = 0.15 # jump cooldown
        self.jump_time = 0
        self.max_jump_time = 0.4 # jump duration
        self.air_time = 0
        self.air_delay = 0.1 # airborne
        self.current_platform = MainPlatform
        self.platform_group = None
        
    def update(self, keys, dt, platforms):
        self.platform_group = platforms

        if self.player_hit and pygame.time.get_ticks() - self.hit_time >= self.hit_grace:
            self.player_hit = False
            
        self.move(keys, dt)

        if self.is_flying: self.hitbox_radius = 0
        else:              self.hitbox_radius = self.sizeHitbox

        # Flying bar update
        self.fly_bar_rectMax = pygame.Rect(0, 0, self.fly_barMax * 50, 10)
        self.fly_bar_rectMax.centerx = self.rect.centerx
        self.fly_bar_rectMax.centery = self.rect.bottom + 10
        self.fly_bar_rect = pygame.Rect(self.fly_bar_rectMax.left, self.fly_bar_rectMax.top,
                                        self.fly_bar * 50, 10)
        
            
    def draw(self, surface):
        if self.player_hit: player_color = RED     
        else: player_color = WHITE
        if self.is_flying: player_color = BLUE

        if self.player_hit:
            current_time = pygame.time.get_ticks()
            if current_time - self.hit_time >= self.hit_grace:
                self.player_hit = False
        
        if not (self.player_hit and pygame.time.get_ticks() % 200 < 100): # Efek kedip saat kena hit
            self.draw_Hitbox(surface, player_color)


        pygame.draw.rect(surface, player_color, self.rect, 2)

        if self.fly_bar < self.fly_barMax:
            pygame.draw.rect(surface, BLUE, self.fly_bar_rect)
            pygame.draw.rect(surface, CYAN, self.fly_bar_rectMax, 2)


    def on_platform(self):
        for platform in self.platform_group:
            if self.rect.right > platform.rect.left and self.rect.left < platform.rect.right:
                if (self.rect.bottom >= platform.rect.top and # ketika player tepat berada di platform / overlap dalam platform
                    self.rect.bottom <= platform.rect.top + platform.height / 2 # toleransi overlap, semakin kecil semakin ketat
                ):
                    self.current_platform = platform
                    return True
        return False
    
    def move(self, keys, dt):
        #Flying movement
        if keys[pygame.K_LSHIFT]:
            if self.fly_bar > 0:
                self.fly_bar -= dt
                self.hitbox_radius = 0
                self.is_flying = True 
            else:
                self.hitbox_radius = self.sizeHitbox
                self.is_flying = False
            self.fly_barCD_time = pygame.time.get_ticks() / 1000  # set CD after flying

        else:
            curCD_time = pygame.time.get_ticks() / 1000
            if curCD_time - self.fly_barCD_time >= self.fly_barCD: # Recharge after CD
                self.fly_bar = min(self.fly_barMax, self.fly_bar + self.fly_barRate * dt)
            
            self.hitbox_radius = self.sizeHitbox
            self.is_flying = False

        if self.is_flying:
            dx = 0
            dy = 0
            if keys[pygame.K_a]: dx = -1
            if keys[pygame.K_d]: dx = 1

            if keys[pygame.K_w]: dy = -1
            if keys[pygame.K_s]: dy = 1

            if dx != 0 and dy != 0:
                length = (dx**2 + dy**2) ** 0.5
                dx /= length
                dy /= length
        
            if self.rect.left > 0 and self.rect.right < WIDTH:
                self.rect.centerx += dx * self.speedX * dt
            
            if self.rect.top > 0 and self.rect.bottom <= MainPlatform.rect.top:
                self.rect.centery += dy * self.speedY * dt
            
            if self.rect.left < 0 :                      self.rect.left = 0 
            if self.rect.right > WIDTH :                 self.rect.right = WIDTH 
            if self.rect.top < 0 :                       self.rect.top = 0 
            if self.rect.bottom > MainPlatform.rect.top: self.rect.bottom = MainPlatform.rect.top
            return #agar tidak double dari movement biasa 

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
        if (keys[pygame.K_w] or keys[pygame.K_SPACE]) and (not keys[pygame.K_s]
                                                      and self.on_platform() 
                                                      and not self.is_jumping):
            if self.jump_delay >= self.max_jump_delay:
                self.is_jumping = True                  
                self.jump_time = 0
                self.jump_delay = 0
        
        if self.is_jumping:
            if (keys[pygame.K_w] or keys[pygame.K_SPACE]) and (not keys[pygame.K_s]
                                                    and self.rect.top > 0):
                if self.jump_time < self.max_jump_time:  # Durasi lompat jika di tahan sampai max                            
                    self.rect.centery -= self.speedY * dt
                    self.jump_time += dt
                else:
                    self.is_jumping = False
            else:                                 # Jika berhenti ditahan = sudah tidak jumping
                self.is_jumping = False

        #Reset airborne, kondisi jump, etc jika berada di platform
        if self.on_platform() and not self.is_jumping and not keys[pygame.K_s]:
            self.jump_delay += dt
            self.air_time = 0
            if self.current_platform is MainPlatform:
                self.rect.bottom = MainPlatform.rect.top
                 
        #Gravitasi
        if not self.on_platform() and not self.is_jumping:
            self.air_time += dt
            if self.air_time > self.air_delay: # Airborne
                self.rect.centery += self.gravity * dt

class Bullet(GameObject):
    def __init__(self, pattern = None):
        if pattern is None: # Random pattern
            side = random.choice(['top', 'right', 'left'])
            if side == 'top': # Fall down
                x = random.randint(0, WIDTH) 
                y = -20
                self.vx = random.uniform(-100, 100) #v = velocity x or y
                self.vy = random.uniform(150, 300) 

            elif side == 'right': # Move left
                x = WIDTH + 20
                y = random.randint(0, MainPlatform.rect.top)
                self.vx = random.uniform(-300, -150) 
                self.vy = random.uniform(-50, 50)

            else: # left # Move right
                x = -20
                y = random.randint(0, MainPlatform.rect.top)
                self.vx = random.uniform(150, 300) 
                self.vy = random.uniform(-50, 50)


        super().__init__(x, y, hitbox_radius=8)
        self.color = CYAN

    def fire(self, dt):
        self.rect.centerx += self.vx * dt
        self.rect.centery += self.vy * dt
        
    def collided(self, platforms):
        for platform in platforms:
            if self.rect.right > platform.rect.left and self.rect.left < platform.rect.right:
                if self.rect.bottom > platform.rect.top and self.rect.top < platform.rect.bottom:
                    return True
        
        return self.rect.right < -20 or self.rect.left > WIDTH + 20
        

def circle_collide(c1_pos, r1, c2_pos, r2):
    dx = c1_pos[0] - c2_pos[0] 
    dy = c1_pos[1] - c2_pos[1]
    
    return dx*dx + dy*dy <= (r1 + r2) ** 2 # dx^2 + dy^2 <= (r_1 + r_2)^2 rumus kolisi lingkaran



# Platform making per level
Platforms = [MainPlatform]
Platforms.append(GameObject(400, HEIGHT//2, 200, 10))
Platforms.append(GameObject(400, HEIGHT//3, 200, 10))
Platforms.append(GameObject(900, HEIGHT//2, 200, 15))
Platforms.append(GameObject(15, HEIGHT//2, 200))
Platforms.append(GameObject(1500, HEIGHT//2, 200, 10))

Platforms2 = [MainPlatform]
Platforms2.append(GameObject(400, HEIGHT//4, 200, 10))

# Player 
tes = Player()
hit_counter = 0

# Enemy
enemies = [] # List bullet
spawn_timer = 0
spawn_rate = 0.5

clock = pygame.time.Clock()
running = True
while running: #.tick(framerate) mengembalikan waktu ms antar frame
    dt = clock.tick(60) / 1000  # mengembalikan ms / 1000 = sekon
    keys = pygame.key.get_pressed()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    tes.update(keys, dt, Platforms)

    # Spawn bullets
    spawn_timer += dt
    if spawn_timer >= spawn_rate:
        enemies.append(Bullet())
        spawn_timer = 0
        spawn_rate = max(0.10, spawn_rate - 0.005)
    
    for enemy in enemies[:]:
        enemy.fire(dt)
        
        #Check i-frame & kolisi
        if not tes.is_flying and not tes.player_hit:
            if circle_collide(tes.rect.center, tes.hitbox_radius, enemy.rect.center, enemy.hitbox_radius):
                enemies.remove(enemy)
                hit_counter = hit_counter + 1
                print(f"Ouch! You got hit! x{hit_counter} time(s)\n")
                tes.hit_time = pygame.time.get_ticks()
                tes.player_hit = True
                continue

        if enemy.collided(Platforms):
            enemies.remove(enemy)

    
    # Draw objects 
    screen.fill(BLACK)
    
    

    for platform in Platforms:
        pygame.draw.rect(screen, GREEN, platform.rect)
    
    tes.draw(screen)
    
    for enemy in enemies:
        enemy.draw_Hitbox(screen, enemy.color)
    


    pygame.display.update()

pygame.quit()
sys.exit()