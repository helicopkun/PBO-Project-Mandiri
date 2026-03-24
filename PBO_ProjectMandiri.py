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
        self.speedY = 500
        self.gravity = 450

        self.is_flying = False
        self.fly_dur = 2000 /1000 # 2 sec
        self.is_jumping = False 
        self.jump_delay = 0                          
        self.max_jump_delay = 200 /1000 # 200 ms , 1 sec = 1000 ms
        self.jump_time = 0
        self.max_jump_time = 250 /1000 # 250 ms
        self.air_time = 0
        self.air_delay = 100 /1000 # 150 ms
        

    def on_platform(self):
        return self.rect.bottom >= MainPlatform.top - 3

    def move(self, keys, dt):
        #Flying
        if keys[pygame.K_LSHIFT]:
            self.hitbox_radius = 0
            self.gravity = 0
            self.is_flying = True
        else:
            self.hitbox_radius = self.sizeHitbox
            self.gravity = 450
            self.is_flying = False

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
        
        if self.is_jumping or self.is_flying:
            if (keys[pygame.K_w] or keys[pygame.K_SPACE]) and (not keys[pygame.K_s]
                                                    and self.rect.top > 0):
                if self.jump_time < self.max_jump_time or self.is_flying:                                   
                    self.rect.centery -= self.speedY * dt
                    self.jump_time += dt
                else:
                    self.is_jumping = False
            elif not self.is_flying:
                self.is_jumping = False

        #Reset airborne, kondisi jump, etc jika berada di platform
        if self.on_platform():
            self.jump_delay += dt
            self.air_time = 0
            self.rect.bottom = MainPlatform.top - 3
            self.is_jumping = False
        else:
            self.air_time += dt
            
        #Gravitasi
        if not self.on_platform() and not self.is_jumping and not self.is_flying:
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


clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 48, bold=True)

def get_text(Message, color = BLACK, alpha = 255, BGColor = None):
    text = font.render(Message, True, color, BGColor)
    text.set_alpha(alpha)
    return text
delayText = 1000



running = True
while running: #.tick(framerate) mengembalikan waktu ms antar frame
    dt = clock.tick(60) / 1000  # mengembalikan ms / 1000 = sekon
    screen.fill(BLACK)
    keys = pygame.key.get_pressed()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
    spawn_timer += dt
    if spawn_timer >= spawn_rate:
        enemies.append(Bullet())
        spawn_timer = 0
        spawn_rate = max(0.15, spawn_rate - 0.005)
    
    tes.move(keys, dt)

    for enemy in enemies[:]:
        enemy.fire(dt) #double speed
        enemy.fire(dt)
        
        #Check i-frame & kolisi
        if not tes.is_flying:
            if circle_collide(tes.rect.center, tes.hitbox_radius, enemy.rect.center, enemy.hitbox_radius):
                # For now, just print to the console and turn the player red when hit
                enemies.remove(enemy)
                print("Ouch! You got hit!")
                pygame.draw.rect(screen, RED, tes.rect)

        if enemy.is_offscreen():
            enemies.remove(enemy)

    player_color = BLUE if tes.is_flying else WHITE
    pygame.draw.rect(screen, player_color, tes.rect, 2)
    tes.draw_Hitbox(screen)
    
    for enemy in enemies:
        enemy.draw_Hitbox(screen, enemy.color)
    pygame.draw.rect(screen, BLUE, MainPlatform)

    if pygame.time.get_ticks() % 1000 < 20: 
        print(f"Jumlah musuh di layar: {len(enemies)}")
    pygame.display.update()

pygame.quit()
sys.exit()