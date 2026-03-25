import pygame
import sys
import random

pygame.init()

WIDTH = 600
HEIGHT = 400

screen = pygame.display.set_mode((WIDTH, HEIGHT))
MainPlatform = pygame.Rect(0, HEIGHT//1.5, WIDTH, HEIGHT//2)   
pygame.display.set_caption("Dodge / parry this")

CYAN = (0, 255, 255)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

def circle_collide(c1_pos, r1, c2_pos, r2):
    dx = c1_pos[0] - c2_pos[0] 
    dy = c1_pos[1] - c2_pos[1]
    
    return dx*dx + dy*dy <= (r1 + r2) ** 2 # dx^2 + dy^2 <= (r_1 + r_2)^2 adalah rumus kolisi lingkaran

class GameObject: #Circle Hitbox
    def __init__ (self, x, y, hitbox_radius = 10):
        self.hitbox_radius = hitbox_radius
        self.size = self.hitbox_radius * 2
        self.rect = pygame.Rect(0, 0,
                                self.size, self.size)
        self.rect.center = (x, y)
    
    def draw_Hitbox(self, surface, color = WHITE): #draw hitbox circle
        pygame.draw.circle(surface, color,
                            self.rect.center, self.hitbox_radius) 

class Player(GameObject):
    sizeHitbox = 5 #customize player size & hitbox offset
    offset = 10
    
    def __init__(self, x = sizeHitbox + 10, y = MainPlatform.top, hitbox_radius=sizeHitbox):
        super().__init__(x, y, hitbox_radius)
        self.size += self.offset
        self.rect.width = self.size
        self.rect.height = self.size

        self.speedX = 400
        self.speedY = 400
        self.gravity = 250

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
        
        

    def on_platform(self):
        return self.rect.bottom >= MainPlatform.top - 3

    
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
                if self.fly_bar < self.fly_barMax:
                    self.fly_bar += self.fly_barRate * dt
                else:
                    self.fly_bar = self.fly_barMax
            
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
        
            if self.rect.left > 0 + 5 or self.rect.right < WIDTH - 5:
                self.rect.centerx += dx * self.speedX * dt
                
            if self.rect.top > 0 + 3 or self.rect.bottom < MainPlatform.top - 3:
                self.rect.centery += dy * self.speedY * dt
            
            if self.rect.left < 0 + 5:                  self.rect.left = 0 + 5
            if self.rect.right > WIDTH - 5:             self.rect.right = WIDTH - 5
            if self.rect.top < 0 + 3:                   self.rect.top = 0 + 3
            if self.rect.bottom > MainPlatform.top - 3: self.rect.bottom = MainPlatform.top - 3
            return #agar tidak double dari movement biasa 


        #Horizontal movement
        if keys[pygame.K_a] and self.rect.left > 0 + 5:
                self.rect.centerx -= self.speedX * dt
                if self.rect.left < 0 + 5:
                    self.rect.left = 0 + 5
        if keys[pygame.K_d] and self.rect.right < WIDTH - 5:
                self.rect.centerx += self.speedX * dt
                if self.rect.right > WIDTH - 5:
                    self.rect.right = WIDTH - 5

        #Vertical movement
        if keys[pygame.K_s] and not self.on_platform():
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
            else:                                    # Jika berhenti ditahan = sudah tidak jumping
                self.is_jumping = False

        #Reset airborne, kondisi jump, etc jika berada di platform
        if self.on_platform():
            self.jump_delay += dt
            self.air_time = 0
            self.rect.bottom = MainPlatform.top - 3
            self.is_jumping = False
                 
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
                y = random.randint(0, MainPlatform.top)
                self.vx = random.uniform(-300, -150) 
                self.vy = random.uniform(-50, 50)

            else: # left # Move right
                x = -20
                y = random.randint(0, MainPlatform.top)
                self.vx = random.uniform(150, 300) 
                self.vy = random.uniform(-50, 50)


        super().__init__(x, y, hitbox_radius=8)
        self.color = CYAN

    def fire(self, dt):
        self.rect.centerx += self.vx * dt
        self.rect.centery += self.vy * dt
        
    def is_offscreen(self):
        # Returns True if the projectile has completely left the screen
        return (self.rect.right < -20 or self.rect.left > WIDTH + 20 or 
                self.rect.top > MainPlatform.top)


tes = Player()
enemies = [] # List bullet
spawn_timer = 0
spawn_rate = 0.5
hit_counter = 0
hit_grace = 2200 #ms i-frame after getting hit
player_hit = False

clock = pygame.time.Clock()

running = True
while running: #.tick(framerate) mengembalikan waktu ms antar frame
    dt = clock.tick(60) / 1000  # mengembalikan ms / 1000 = sekon
    screen.fill(BLACK)
    pygame.draw.rect(screen, GREEN, MainPlatform)
    keys = pygame.key.get_pressed()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
    spawn_timer += dt
    if spawn_timer >= spawn_rate:
        enemies.append(Bullet())
        spawn_timer = 0
        spawn_rate = max(0.10, spawn_rate - 0.005)
    
    tes.move(keys, dt)

    for enemy in enemies[:]:
        enemy.fire(dt)
        
        #Check i-frame & kolisi
        if not tes.is_flying and not player_hit:
            if circle_collide(tes.rect.center, tes.hitbox_radius, enemy.rect.center, enemy.hitbox_radius):
                enemies.remove(enemy)
                hit_counter = hit_counter + 1
                print(f"Ouch! You got hit! x{hit_counter} time(s)\n")
                hit_time = pygame.time.get_ticks()
                player_hit = True

        if enemy.is_offscreen():
            enemies.remove(enemy)

    if player_hit:
        player_color = RED
        current_time = pygame.time.get_ticks()
        if current_time - hit_time >= hit_grace:
            player_hit = False
            tes.draw_Hitbox(screen)
            player_color = WHITE
    else:
        tes.draw_Hitbox(screen)
        player_color = WHITE
    
    if tes.is_flying: player_color = BLUE
    

    pygame.draw.rect(screen, player_color, tes.rect, 2)

    fly_bar_rect = pygame.Rect(0, 0, tes.fly_bar * 50, 10)
    fly_bar_rect.centerx = tes.rect.centerx
    fly_bar_rect.centery = tes.rect.centery + 20

    fly_bar_rectMax = pygame.Rect(0, 0, tes.fly_barMax * 50 + 5, 15)
    fly_bar_rectMax.centerx = tes.rect.centerx
    fly_bar_rectMax.centery = tes.rect.centery + 20

    pygame.draw.rect(screen, BLUE, fly_bar_rect)
    pygame.draw.rect(screen, CYAN, fly_bar_rectMax, 2)
    
    for enemy in enemies:
        enemy.draw_Hitbox(screen, enemy.color)
    


    pygame.display.update()

pygame.quit()
sys.exit()