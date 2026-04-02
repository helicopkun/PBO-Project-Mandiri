import pygame
import sys
import random
import math

pygame.init()
pygame.font.init()

WIDTH = 1920
HEIGHT = 1080

screen = pygame.display.set_mode((WIDTH, HEIGHT)) # Untuk UI
pygame.display.set_caption("Maidenless Danmaku") # LMAOO AI got a hilarious name for ts
# Maidenless ~ a reference to Elden ring where the npc calls us maidenless
# Danmaku ~ bullet hell in japanese
font_size = 40
UI_FONT = pygame.font.Font("assets/Cirno.ttf", font_size)
UI_FONT.set_bold(True)

CYAN = (0, 255, 255)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GOLD = (255, 215, 0)
PURPLE = (148, 0, 211)
ORANGE = (255, 165, 0)
BROWN = (150, 75, 0)
GREY = (128, 128, 128)
YELLOW = (255, 255, 0)
RED2_0 = (238, 75, 43)
CYAN2_0 = (192, 253, 253)



# ================================================= Cache =========================================================================================================================================
assets = {} 
def load_asset(image_path): #load base image into cache
    path = "assets/" + image_path
    if path not in assets:
        assets[path] = pygame.image.load(path).convert_alpha()
    return assets[path]

image_cache = {} 
def get_image(image_path, rect=None, # load or make a new image in cache (into the assigned rectangle if available)
               flipx = 0, flipy = 0, angle = 0, 
               size_offsetx = 0, size_offsety = 0): # offset for minor adjustment, not needed if image is fixed by editing
    scale = None
    if rect: scale = (rect.width + size_offsetx, rect.height + size_offsety)
    key = (image_path, scale, flipx, flipy, angle)
 
    if key not in image_cache:
        image = load_asset(image_path)
        image = pygame.transform.flip(image, flipx, flipy)
        if scale: image = pygame.transform.scale(image, scale)
        image = pygame.transform.rotate(image, angle)
        image_cache[key] = image
    return image_cache[key]


# ================================================= Class =========================================================================================================================================

class GameObject: #Combination of Circle and Rect hitbox, based on usage (finished?) todo: will probably change if needed
    def __init__ (self, x, y, width = 20, height = 20, hitbox_radius = 10, 
                                                            image_path = None,
                                                            flipx = 0, flipy = 0, angle = 0, 
                                                            size_offsetx = 0, size_offsety = 0):
        self.hitbox_radius = hitbox_radius
        self.width = width
        self.height = height
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.rect.center = (x, y)
        
        self.image_path = image_path
        self.image = None
        #use local variable for load for one time use
        if self.image_path: self.image = get_image(image_path, self.rect, flipx, flipy, angle, size_offsetx, size_offsety)
        
    def draw_self(self, surface):
        if self.image: #note to self, change image on self.image by self.image = get_image(new image)
            image_rect = self.image.get_rect(center=self.rect.center)
            surface.blit(self.image, image_rect) 
            if show_img_rect: pygame.draw.rect(surface, WHITE, image_rect, 2)
        else: pygame.draw.rect(surface, WHITE, self.rect, 2) # no texture

    def draw_hitcircle(self, surface, color = WHITE, hitbox_radius = None, border_width = 2): #draw hitbox circle
        hitbox_radius = self.hitbox_radius if hitbox_radius is None else hitbox_radius
        pygame.draw.circle(surface, color, self.rect.center, hitbox_radius, border_width) 

class Player(GameObject): #todo : will fix keyboard input only and fix draw attack
    def __init__(self, max_hp=5, name = "Baka", image = "cirno.png", attack = 'slash'):
        super().__init__(x= 50, y=MainPlatform.rect.top, width=50, height=100, hitbox_radius=15,
                         image_path="character/"+image, size_offsetx=70, size_offsety=30)
        self.name = name
        self.sizeHitbox = self.hitbox_radius
        self.speedX = 400
        self.speedY = 400
        self.gravity = 350

        self.max_hp = max_hp
        self.hp = self.max_hp
        self.absorb_count = 0 

        self.grace_active = False # i-frame setelah kena hit
        self.grace_time = 0
        self.grace_duration = 1.5

        self.is_phasing = False
        self.phase_speed = 1.5
        self.phase_barMax = 2 #sekon
        self.phase_barRate = 0.5 #bar recharge per second
        self.phase_barCD = 0.6 #cooldown before recharge
        self.phase_barCD_time = 0
        self.phase_bar = 0 # current bar

        self.is_jumping = False 
        self.jump_delay = 0                          
        self.max_jump_delay = 0.15 # jump cooldown
        self.jump_time = 0
        self.max_jump_time = 0.4 # jump duration
        self.air_time = 0
        self.air_delay = 0.1 # airborne
        self.current_platform = MainPlatform
        self.platform_group = None
        
        self.action_cd_timer = 0 # action cooldown
        self.action_barMax = 1.3

        self.absorb_active = False
        self.absorb_duration = 0.3  # Window absorb
        self.absorb_cd = 1
        self.absorb_radius = 30
        self.absorb_color = CYAN

        self.facing = 'right'
        self.facing_angle = 0
        self.facing_right = True
        self.look_delay_timer = 0
        self.look_delay = False
        
        self.attack_active = False
        self.attack_type = attack
        self.attack_type_data = attack_type[attack]
        self.attack_hitboxes = []
        self.attack_hitboxes_active = [] #idk if this is useful
        self.attack_duration = self.attack_type_data['duration']# Window attack
        self.attack_cd = self.attack_type_data['cd']
        self.attack_scale = self.attack_type_data['scale']
        self.attack_frame_count = self.attack_type_data['frame_count']
        self.attack_active_frame = self.attack_type_data['active_frames']   
        self.attack_frame_timer = 0 # for attack frame delay
        self.attack_cur_frame = 0
        self.attack_image_center = self.rect.center
        self.copy_rect = None #copying self old pos
          
    def update(self, keys, dt, platforms):
        self.platform_group = platforms
        
        #Movement - freeze when absorbing
        if not self.absorb_active:
            self.move(keys, dt) 
        
        self.current_state()

        self.facing_indicator()
        self.bar_indicator()
        
        # ======= Actions =======
        if not (self.is_phasing or self.action_cd_timer > 0 or self.grace_active):
            #Absorb
            if (keys[pygame.K_l] or action == 3):
                                                        
                self.absorb_active = True
                self.absorb_timer = self.absorb_duration
                self.action_cd_timer = self.absorb_cd
                
            #Attack
            if (keys[pygame.K_k] or action == 1):
                self.attack_active = True
                self.attack_timer = self.attack_duration
                self.action_cd_timer = self.attack_cd
                self.attack_images = [] #get image
                for i in range(self.attack_frame_count + 1):
                    self.attack_images.append(get_image(f"attack/{self.attack_type}/{self.attack_type}-{i}.png", angle=self.facing_angle))
                    offset_dist = 300
                    angle = math.radians(self.facing_angle)
                self.attack_image_center = ( # get setup pos (static pos)
                    self.rect.centerx + math.cos(angle) * offset_dist,
                    self.rect.centery + math.sin(-angle) * offset_dist
                )
                self.copy_rect = self.rect.copy()
                
    def draw(self, surface):
        #Character
        self.image = get_image(image_path=self.image_path, flipx=0 if self.facing_right else 1, rect=self.rect, 
                                                                                            size_offsetx=70, 
                                                                                            size_offsety=30)
        if not (self.grace_active and pygame.time.get_ticks() % 200 < 100): #efek kedip saat kena hit
            self.draw_self(surface)

        if self.absorb_active:
            pygame.draw.circle(surface, self.absorb_color, self.rect.center, self.hitbox_radius + self.absorb_radius, 5)

        if self.attack_active:
            # Check if the animation isnt finished
            if self.attack_cur_frame < self.attack_frame_count:
                current_img = self.attack_images[self.attack_cur_frame]
                atk_img_rect = current_img.get_rect(center=(self.attack_image_center))
                print(self.attack_cur_frame)
                surface.blit(current_img, atk_img_rect)
                if show_atk_hitbox:
                    for hitbox in self.attack_hitboxes:
                        pygame.draw.rect(surface, YELLOW, hitbox, 2)
                    for hitbox in self.attack_hitboxes_active:
                        pygame.draw.rect(surface, RED2_0, hitbox, 2)                
            else:
                # Animation finished
                self.attack_cur_frame = 0
            
            frame_delay = self.attack_duration*750 / self.attack_frame_count 
            if pygame.time.get_ticks() - self.attack_frame_timer > frame_delay:
                self.attack_frame_timer = pygame.time.get_ticks()
                self.attack_cur_frame += 1

            
            
        if self.action_cd_timer > 0:
            pygame.draw.rect(surface, GREY, self.action_bar_rectMax) # BG
            pygame.draw.rect(surface, YELLOW, self.action_bar_rect)
            pygame.draw.rect(surface, WHITE, self.action_bar_rectMax, 2)

        if self.phase_bar < self.phase_barMax:
            pygame.draw.rect(surface, GREY, self.phase_bar_rectMax) # BG
            pygame.draw.rect(surface, BLUE, self.phase_bar_rect)
            pygame.draw.rect(surface, WHITE, self.phase_bar_rectMax, 2)

        #Facing indicator - might change to texture
        line_length = 20
        line_width = 7
        if self.facing == 'left':
            pygame.draw.line(surface, WHITE, (self.rect.left - 20, self.rect.centery),
                                             (self.rect.left - line_length - 20, self.rect.centery), line_width)
        if self.facing == 'right':
            pygame.draw.line(surface, WHITE, (self.rect.right + 20, self.rect.centery),
                                             (self.rect.right + line_length + 20, self.rect.centery), line_width)
        if self.facing == 'up':
            pygame.draw.line(surface, WHITE, (self.rect.centerx, self.rect.top - 20),
                                             (self.rect.centerx, self.rect.top - line_length - 20), line_width)
        if self.facing == 'down':
            pygame.draw.line(surface, WHITE, (self.rect.centerx, self.rect.bottom + 20),
                                             (self.rect.centerx, self.rect.bottom + line_length + 20), line_width)

        if self.facing == 'top-left':
            pygame.draw.line(surface, WHITE, (self.rect.left - 20, self.rect.top - 20),
                                            get_end_pos(self.rect.left - 20, self.rect.top - 20, 45, line_length), line_width)
        if self.facing == 'top-right':
            pygame.draw.line(surface, WHITE, (self.rect.right + 10, self.rect.top - 10),
                                            get_end_pos(self.rect.right + 10, self.rect.top - 10, -45, line_length), line_width)
        if self.facing == 'bottom-left':
            pygame.draw.line(surface, WHITE, (self.rect.left - 20, self.rect.bottom + 20),
                                            get_end_pos(self.rect.left - 20, self.rect.bottom + 20, -45, line_length), line_width)
        if self.facing == 'bottom-right':
            pygame.draw.line(surface, WHITE, (self.rect.right + 10, self.rect.bottom + 10),
                                            get_end_pos(self.rect.right + 10, self.rect.bottom + 10, 45, line_length), line_width)

    def on_platform(self):
        for platform in self.platform_group:
            if self.rect.right > platform.rect.left and self.rect.left < platform.rect.right: # ketika ujung player memasuki area platform
                if (self.rect.bottom >= platform.rect.top and # ketika player tepat berada di platform / overlap dalam platform
                    self.rect.bottom <= platform.rect.top + platform.height / 2 # toleransi overlap, semakin kecil semakin ketat
                ):
                    self.current_platform = platform
                    return True
        return False
    
    def move(self, keys, dt):
        if keys[pygame.K_w]: # set delay timer after jump
            self.look_delay_timer = pygame.time.get_ticks()
            self.look_delay = True
            
        #Flying movement
        if keys[pygame.K_LSHIFT] and self.action_cd_timer <= 0:
            if self.phase_bar > 0:
                self.phase_bar -= dt
                self.hitbox_radius = 0
                self.is_phasing = True 
            else:
                self.is_phasing = False
            self.phase_barCD_time = pygame.time.get_ticks() / 1000  # set CD after phaseing

        else:
            curCD_time = pygame.time.get_ticks() / 1000
            if curCD_time - self.phase_barCD_time >= self.phase_barCD: # Recharge after CD
                self.phase_bar = min(self.phase_barMax, self.phase_bar + self.phase_barRate * dt)
            
            self.is_phasing = False

        if self.is_phasing:
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
        
            self.rect.centerx += dx * self.speedX * dt * self.phase_speed
            self.rect.left = max(0, self.rect.left)
            self.rect.right = min(WIDTH, self.rect.right)
            
            self.rect.centery += dy * self.speedY * dt * self.phase_speed
            self.rect.top = max(0, self.rect.top)
            self.rect.bottom = min(MainPlatform.rect.top, self.rect.bottom)
            
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
        if keys[pygame.K_w] and (not keys[pygame.K_s]
                                 and self.on_platform() 
                                 and not self.is_jumping):
            if self.jump_delay >= self.max_jump_delay:
                self.is_jumping = True                  
                self.jump_time = 0
                self.jump_delay = 0
        
        if self.is_jumping:
            if keys[pygame.K_w] and (not keys[pygame.K_s]
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

    def facing_indicator(self):
        #Movement facing indicator
        if not (self.attack_active or self.absorb_active):
            if pygame.time.get_ticks() - self.look_delay_timer >= 200: # delay
                self.look_delay = False
                self.facing = 'right' if self.facing_right else 'left'

            if keys[pygame.K_a] and not keys[pygame.K_d]: self.facing_right = False
            if keys[pygame.K_d] and not keys[pygame.K_a]: self.facing_right = True
                
            if keys[pygame.K_w] and not keys[pygame.K_s]: self.facing = 'up'
            if keys[pygame.K_s] and not keys[pygame.K_w]: self.facing = 'down'

            if keys[pygame.K_w]: 
                if keys[pygame.K_d]: self.facing = 'top-right'
                if keys[pygame.K_a]: self.facing = 'top-left'

            if keys[pygame.K_s]:
                if keys[pygame.K_d]: self.facing = 'bottom-right'
                if keys[pygame.K_a]: self.facing = 'bottom-left'
                
        # Attack facing indicator
        if self.action_cd_timer <= 0:
            direction = ['right', 'top-right', 'up', 'top-left', 'left', 'bottom-left', 'down', 'bottom-right']
            if action == 1:
                mx , my = click_pos
                dx = mx - self.rect.centerx
                dy = my - self.rect.centery

                self.facing_angle = math.degrees(math.atan2(-dy, dx)) #-dy because pygame y is flipped
                # shifts from 0 <-> 44 to -22.5 <-> 22.5 for index 0      
                index = int((self.facing_angle + 22.5) // 45) % 8 # 22.5 for shifting angle, e.g: without 0 - 44 -> 0 instead turn into (-22.5 + 22.5) to (22.5 + 22.5) -> 0
                self.facing = direction[index] # convert 24-d to 8-d
                
                self.facing_angle = round(self.facing_angle / 15) * 15 #rounding (snapping)

                # Reset facing after different direction from current direction attack
                if self.facing in {'right', 'top-right', 'bottom-right'}:
                    self.facing_right = True
                if self.facing in {'left', 'top-left', 'bottom-left'}: 
                    self.facing_right = False

            elif keys[pygame.K_k]:
                for i in range(8):
                    if self.facing == direction[i]:
                        self.facing_angle = i * 45

    def current_state(self): #Update cooldown, grace, duration
        #Check phasing for hitbox radius
        if self.is_phasing: self.hitbox_radius = 0
        else: self.hitbox_radius = self.sizeHitbox
        
        #Hit Grace      
        if self.grace_active and pygame.time.get_ticks() - self.grace_time >= self.grace_duration * 1000:
            self.grace_active = False
        
        #Action CD, cannot different action at same time, different CD based on last action
        if self.action_cd_timer > 0:
            self.action_cd_timer -= dt

        # Absorb duration
        if self.absorb_active:
            self.absorb_timer -= dt
            if self.absorb_timer <= 0:
                self.absorb_active = False

        # Attack duration
        if self.attack_active:
            self.attacking()
            self.attack_timer -= dt
            if self.attack_timer <= 0:
                self.attack_hitboxes.clear() # reset hitbox (also frame in case of bad timing)
                self.attack_hitboxes_active.clear()
                self.attack_active = False
                self.attack_cur_frame = 0

    def attacking(self):
        self.attack_hitboxes = self.generate_attack_hitbox()
        if self.attack_active_frame[0] <= self.attack_cur_frame <= self.attack_active_frame[1]:
            self.attack_hitboxes_active = self.attack_hitboxes
        else: self.attack_hitboxes_active = []
            
    def generate_attack_hitbox(self): # generate chain hitbox trajectory
        n = 10  # more = smoother coverage

        if self.attack_type == 'slash':
            length = 2 * self.height
            thickness = self.width
        if self.attack_type == 'pierce': 
            length = 4 * self.height
            thickness = self.width

        length *= self.attack_scale
        thickness *= self.attack_scale

        angle = math.radians(self.facing_angle)
        dx = math.cos(angle)
        dy = math.sin(-angle)

        hitbox_list = []
        for i in range(n): #generate n amount of hitbox on a chain hitbox, for e.g: [P]->[][][][][] <-- player's attack hitbox
            steps = i / (n + 1)

            x = self.copy_rect.centerx + dx * length * steps
            y = self.copy_rect.centery + dy * length * steps

            rect = pygame.Rect(0, 0, thickness, thickness)
            rect.center = (x, y)
            hitbox_list.append(rect)
        return hitbox_list
    
    def bar_indicator(self):
        # Action bar update
        self.action_bar_rectMax = pygame.Rect(0, 0, 10, 
                                        self.rect.height / 2 * self.action_barMax)
        self.action_bar_rectMax.centerx = (self.rect.right + 20) if not self.facing_right else (self.rect.left - 20) #kebalikan facing
        self.action_bar_rectMax.centery = self.rect.centery
        
        self.action_bar_rect = pygame.Rect(0, 0, self.action_bar_rectMax.width, 
                                        self.rect.height / 2 * (self.action_barMax - self.action_cd_timer))
        self.action_bar_rect.x = self.action_bar_rectMax.x
        self.action_bar_rect.bottom = self.action_bar_rectMax.bottom

        # Phasing bar update
        self.phase_bar_rectMax = pygame.Rect(0, 0, self.rect.width * self.phase_barMax, 10)
        self.phase_bar_rectMax.centerx = self.rect.centerx
        self.phase_bar_rectMax.centery = self.rect.bottom + 10
        self.phase_bar_rect = pygame.Rect(self.phase_bar_rectMax.left, self.phase_bar_rectMax.top,
                                        self.rect.width * self.phase_bar, 
                                        self.phase_bar_rectMax.height)

class Boss(GameObject): #boss use rectangular hitbox (almost finished) todo: check modularity
    def __init__(self, name, phase_data, w=140, h=140, start_x = WIDTH//2, direction = 1, circle_color = WHITE, image = "enemy.png"): # 1 to go right, -1 to go left 
        self.phases = phase_data                                                                                  
        self.total_phases = len(phase_data)
        self.current_phase = 1
        # data phase 1
        start_y = self.phases[self.current_phase]['y_axis']
        super().__init__(x=start_x, y=start_y, width=w, height=h, hitbox_radius=30, image_path="boss/" + image, 
                                                                                    size_offsetx=125, size_offsety=125)
        self.name = name
        self.circle_color = circle_color
        self.max_hp = self.phases[self.current_phase]['max_hp']
        self.hp = self.max_hp
        self.grace_active = False
        self.grace_time = 0
        self.grace_duration = 200
        self.alive = True

        self.base_y = float(start_y)
        self.bop_amplitude = 25
        self.bop_frequency = 3

        self.direction = direction # 1 for right, -1 for left
        self.fire_timer = 0
        
    def update(self, dt, player, bullet_list):
        if not self.alive: return
        
        if self.grace_active and pygame.time.get_ticks() - self.grace_time >= self.grace_duration:
            self.grace_active = False

        phase = self.phases[self.current_phase]
        target_phase_y = phase['y_axis']

        #Transition phase movement
        if abs(self.base_y - target_phase_y) > 2:
            if self.base_y < target_phase_y:
                self.base_y += 100 * dt
            else:
                self.base_y -= 100 * dt

        # Bop movement
        time = pygame.time.get_ticks() / 1000
        bop_offset = math.sin(time * self.bop_frequency) * self.bop_amplitude

        self.rect.centery = self.base_y + bop_offset

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
            if pygame.time.get_ticks() - player.grace_time >= 1000: #delay after player get hit & first spawn
                self.shoot(player, bullet_list, phase)
          
    def shoot(self, player, bullet_list, phase_data):
        pattern = phase_data['pattern']
        num_bullets = phase_data['num_bullet']
        spd = phase_data['bullet_spd']
        size = phase_data['bullet_size']
        color = phase_data['color']
        image = phase_data['image'] + '.png'
        cx, cy = self.rect.center
        
        if pattern == 'fan':
            angle_to_player = math.atan2(player.rect.centery - cy, player.rect.centerx - cx)
            spread = math.radians(20) # 20 degrees between each bullet
            
            # middle bullet aims exactly at the player
            start_angle = angle_to_player - (spread * (num_bullets // 2))
            
            for i in range(num_bullets):
                a = start_angle + spread * i 
                bx = math.cos(a) * spd
                by = math.sin(a) * spd
                angle = -math.degrees(math.atan2(by, bx))
                angle = round(angle / 5) * 5 #snap to 5* 0, 5, 10 etc for performance, angle is float so round it
                bullet_list.append(Bullet(cx, cy, bx, by, size, color, image, angle=angle))
                
        if pattern == 'circle':
            step = (math.pi * 2) / num_bullets
            for i in range(num_bullets):
                a = step * i
                bx = math.cos(a) * spd
                by = math.sin(a) * spd
                angle = -math.degrees(math.atan2(by, bx))
                angle = round(angle / 5) * 5
                bullet_list.append(Bullet(cx, cy, bx, by, size, color, image, angle=angle))
                
        if pattern == 'chaos': # Random from inside boss
            for i in range(num_bullets):
                a = random.uniform(0, math.pi * 2)
                bx = math.cos(a) * spd
                by = math.sin(a) * spd
                angle = -math.degrees(math.atan2(by, bx))
                angle = round(angle / 5) * 5
                bullet_list.append(Bullet(cx, cy, bx, by, size, color, image, angle=angle))

        if pattern == 'random': # Random entire screen
            for i in range(num_bullets):
                side = random.choice(['top', 'right', 'left'])
                if side == 'top': # Fall down
                    cx = random.randint(0, WIDTH) 
                    cy = -20
                    bx = random.uniform(-100, 100)
                    by = random.uniform(150, 300) 
                elif side == 'right': # Move left
                    cx = WIDTH + 20
                    cy = random.randint(0, MainPlatform.rect.top)
                    bx = random.uniform(-300, -150) 
                    by = random.uniform(-50, 50)
                else: # left # Move right
                    cx = -20
                    cy = random.randint(0, MainPlatform.rect.top)
                    bx = random.uniform(150, 300) 
                    by = random.uniform(-50, 50)
                angle = -math.degrees(math.atan2(by, bx))
                angle = round(angle / 5) * 5
                bullet_list.append(Bullet(cx, cy, bx, by, size, color, image, angle=angle))
                
    def take_damage(self):
        self.hp -= 1
        spawn_particles(self.rect.centerx, self.rect.centery, color=RED2_0, count=10) # Hit feedback
        if self.hp <= 0:
            self.current_phase += 1
            self.change_phase()
            
    def change_phase(self):
        spawn_particles(self.rect.centerx, self.rect.centery, color=CYAN, count=30, is_burst=True) # Trigger massive death particle burst each transition 
        if self.current_phase > self.total_phases:
            self.alive = False # Boss defeated!
        else:
            self.max_hp = self.phases[self.current_phase]['max_hp']
            self.hp = self.max_hp
            
    def draw(self, surface): #hitbox
        if not self.alive: return
        color = self.phases[self.current_phase]['color']
        if not (self.grace_active and pygame.time.get_ticks() % 200 < 100): #efek kedip saat kena hit
            self.draw_hitcircle(surface, color, 6) #draw hitbox here is more like indicator in the middle, color for phase color
            self.draw_hitcircle(surface, self.circle_color, 10, 3) #self.color for boss main color
            self.draw_self(surface)
            
class Bullet(GameObject):
    def __init__(self, x, y, vx, vy, hitbox_radius , color=CYAN, image="bullet-orb.png", #default
                                                                 flipx = 0, flipy = 0, angle = 0, 
                                                                 size_offsetx=60, size_offsety=32.5):
        w = h = 2*hitbox_radius
        super().__init__(x, y, w, h, hitbox_radius, f"bullet/{image}", flipx, flipy, angle, size_offsetx, size_offsety)
        self.vx = vx
        self.vy = vy
        self.color = color

    def update(self, dt):
        self.rect.centerx += self.vx * dt
        self.rect.centery += self.vy * dt
        
    def out_of_bounds(self):
        return self.rect.right < -50 or self.rect.left > WIDTH + 50 or self.rect.top > MainPlatform.rect.top or self.rect.bottom < -50

class Particle:
    def __init__(self, x, y, color, is_burst=False):
        self.x = x
        self.y = y
        self.color = color
        self.size = random.uniform(8, 16)
        self.lifetime = random.uniform(0.2, 0.5)
        self.max_lifetime = self.lifetime
        
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(150, 400) if is_burst else random.uniform(50, 150) # make them shoot out faster
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.lifetime -= dt

    def draw(self, surface):
        if self.lifetime > 0:
            current_size = max(0.1, self.size * (self.lifetime / self.max_lifetime)) # Slowly shrink
            pygame.draw.rect(surface, self.color, (self.x, self.y, current_size, current_size))


# ================================================ Functions ==========================================================================================================================================

def get_end_pos(x, y, angle, length): # for line might delete later, after getting a texture for facing indicator
    end_x = x + length * math.cos(angle)
    end_y = y + length * math.sin(angle)
    return (end_x, end_y)

def circle_collide(c1_pos, r1, c2_pos, r2):
    dx = c1_pos[0] - c2_pos[0] 
    dy = c1_pos[1] - c2_pos[1]
    
    return dx*dx + dy*dy <= (r1 + r2) ** 2 # dx^2 + dy^2 <= (r_1 + r_2)^2 rumus kolisi lingkaran

def draw_ui(surface, player, boss_list):
    # Player UI
    p_text = UI_FONT.render(player.name.upper(), True, (192, 253, 253))
    surface.blit(p_text, (20, HEIGHT - font_size - 10))
    # HP Bar
    hp_gap = 1/player.max_hp * 420
    player_hp_bar_rect = pygame.Rect(-25, HEIGHT - font_size - 72, 600, 45)
    image = get_image("ui/hp_bar_player.png", player_hp_bar_rect, size_offsety=30)
    pygame.draw.rect(surface, BLACK, (102, HEIGHT - font_size - 40, 420, 25))
    if player.grace_active: 
        # pygame.draw.rect(surface, RED, (102 + hp_gap/2, HEIGHT - font_size - 40, player.hp/player.max_hp * 400, 25)) #grace hp = almost last hit
        pygame.draw.rect(surface, RED, (102 + hp_gap, HEIGHT - font_size - 40, player.hp/player.max_hp * 420, 25)) #grace hp

    pygame.draw.rect(surface, GREEN, (102, HEIGHT - font_size - 40, player.hp/player.max_hp * 420, 25))

    surface.blit(image, player_hp_bar_rect)
    
    # Absorb/Heal tracking
    absorb_txt = UI_FONT.render(f"Baka Stack: {player.absorb_count}/5", True, CYAN, (250,250,250))
    surface.blit(absorb_txt, (400, HEIGHT - font_size - 10))
    
    # Boss UI
    boss_counter = 0
    offset = -80
    for b in boss_list:
        if b:
            b_text = UI_FONT.render(f"{b.name} (Phase {min(b.current_phase, b.total_phases)}/{b.total_phases})", True, 
                                    WHITE if b.alive else RED2_0)
            b_rect = b_text.get_rect(topright=(WIDTH - 20, HEIGHT - font_size - 65 + offset * boss_counter))
            
            surface.blit(b_text, b_rect)
            
            bar_widthMax = 300
            bar_width = b.hp / b.max_hp * bar_widthMax
            bar_x = WIDTH - 20 - bar_widthMax
            pygame.draw.rect(surface, RED2_0, (bar_x, HEIGHT - font_size - 20 + offset * boss_counter, bar_widthMax, 20))
            pygame.draw.rect(surface, b.phases[min(b.current_phase, b.total_phases)]['color'], 
                            (bar_x, HEIGHT - font_size - 20 + offset * boss_counter, bar_width, 20))
            pygame.draw.rect(surface, WHITE, (bar_x, HEIGHT - font_size - 20 + offset * boss_counter, bar_widthMax, 20), 2)
            pygame.draw.rect(surface, b.circle_color, (bar_x - 30, HEIGHT - font_size - 20 + offset * boss_counter,
                                                                 20, 20))
            boss_counter += 1

def spawn_particles(x, y, color, count=5, is_burst=False):
    for i in range(count):
        particles.append(Particle(x, y, color, is_burst))

def add_plat(plat_list, x, y, w=500, image="platform/platform.png"):
    plat_list.append(GameObject(x , (HEIGHT - y - 150), w, 15, image_path=image,
                                size_offsetx=plat_size_offsetx,
                                size_offsety=plat_size_offsety))

def generate_boss_phase(num_phases=None): # generate boss stat randomly
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
            'max_hp': random.randint(5, 15),
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

def generate_random_boss(amount = 3):
    circle_color_list = [RED, GREEN, YELLOW, BLACK, WHITE]
    for i in range(min(5, amount)): #generate 3 boss, 5 is already too much man
        size = random.randint(100, 200)
        start_x = random.uniform(100, WIDTH - 100)
        direction=random.choice([1 , -1])
        circle_color = random.choice(circle_color_list)
        boss = Boss(f"Boss {i+1}", generate_boss_phase(), size, size, start_x, direction, circle_color)
        circle_color_list.remove(circle_color)
        bosses.append(boss)


# ================================================ Platform making ==========================================================================================================================================

bg = "icy_cave"
background_image = pygame.image.load('assets/background/' + bg + '.png')
background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))

MainPlatform = GameObject(WIDTH//2, HEIGHT, WIDTH, 250, size_offsetx=200, image_path="platform/mainplatform.png",
                                                        size_offsety=1200)
#Platform image offset
plat_size_offsetx=65 
plat_size_offsety=250
plat_pos_offsetx=30
plat_pos_offsety=125

Platform_list = [MainPlatform]
# Stage (unused idea for now)
add_plat(Platform_list, x=150, y=250)
add_plat(Platform_list, x=450, y=400)
add_plat(Platform_list, x=700, y=100)
add_plat(Platform_list, x=1100, y=100)
add_plat(Platform_list, x=1300, y=400)
add_plat(Platform_list, x=1600, y=250)


# ================================================ Player making ==========================================================================================================================================

attack_type = {
            "slash": {"duration": 0.25, "active_frames": (2, 6), "frame_count": 9, 'cd': 0.8, 'scale':3},
            "pierce": {"duration": 0.50, "active_frames": (4, 8), "frame_count": 8,'cd': 1.2, 'scale':3},
            "spin" : {"duration": 0.70, "active_frames": (2, 10),"frame_count": 12,'cd': 1.0, 'scale':3},
        }

PlayerTest = Player(max_hp=15, name="HelicopKun", attack='slash')


# ================================================ Enemy making - manual ==========================================================================================================================================

# Enemy making - color for phase color - bullet image = 'asset/ + {bullet-orb, bullet-1, bullet-2, bullet-3} + .png'
boss1_phase = { 
            1: {'max_hp': 5, 'move_speed': 100, 'y_axis': 150, 'rate': 1.5, 'pattern': 'circle', 
                'num_bullet': 5, 'bullet_spd': 300, 'bullet_size': 10,'color': ORANGE, 'image': 'bullet-1'},

            2: {'max_hp': 8, 'move_speed': 200, 'y_axis': 250, 'rate': 2, 'pattern': 'random', 
                'num_bullet': 5, 'bullet_spd': 350, 'bullet_size': 8,'color': PURPLE, 'image': 'bullet-3'},

            3: {'max_hp': 6, 'move_speed': 250, 'y_axis': 350, 'rate': 1.0, 'pattern': 'circle', 
                'num_bullet': 8, 'bullet_spd': 400, 'bullet_size': 15,'color': BLUE, 'image': 'bullet-2'},

            4: {'max_hp': 4, 'move_speed': 100, 'y_axis': 400, 'rate': 0.8, 'pattern': 'fan', 
                'num_bullet': 7, 'bullet_spd': 400, 'bullet_size': 7,'color': CYAN, 'image': 'bullet-2'},

            5: {'max_hp': 3, 'move_speed': 550, 'y_axis': 150, 'rate': 0.4, 'pattern': 'chaos', 
                'num_bullet': 8, 'bullet_spd': 450, 'bullet_size': 9,'color': GOLD, 'image': 'bullet-orb'}
        }
boss2_phase = { 
            1: {'max_hp': 6, 'move_speed': 350, 'y_axis': 200, 'rate': 0.8, 'pattern': 'chaos', 
                'num_bullet': 4, 'bullet_spd': 400, 'bullet_size': 8, 'color': ORANGE, 'image': 'bullet-3'},

            2: {'max_hp': 8, 'move_speed': 100, 'y_axis': 450, 'rate': 0.5, 'pattern': 'random', 
                'num_bullet': 3, 'bullet_spd': 300, 'bullet_size': 12, 'color': PURPLE, 'image': 'bullet-1'},

            3: {'max_hp': 10, 'move_speed': 400, 'y_axis': 150, 'rate': 1.2, 'pattern': 'circle', 
                'num_bullet': 16, 'bullet_spd': 250, 'bullet_size': 6, 'color': BLUE, 'image': 'bullet-3'},

            4: {'max_hp': 7, 'move_speed': 600, 'y_axis': 300, 'rate': 0.4, 'pattern': 'random', 
                'num_bullet': 5, 'bullet_spd': 500, 'bullet_size': 7, 'color': CYAN, 'image': 'bullet-1'},

            5: {'max_hp': 12, 'move_speed': 700, 'y_axis': 200, 'rate': 0.2, 'pattern': 'chaos', 
                'num_bullet': 10, 'bullet_spd': 450, 'bullet_size': 10, 'color': GOLD, 'image': 'bullet-1'}
        }

boss1 = Boss("Cubecicle", boss2_phase, w=100, h=100, start_x=random.uniform(100, WIDTH - 100), direction=random.choice([1 , -1]), circle_color=CYAN)
boss2 = Boss("And more..", boss1_phase, w=140, h=140, start_x=random.uniform(100, WIDTH - 100), direction=random.choice([1 , -1]), circle_color=CYAN2_0)

# just append boss_list later or declare boss_list = [boss1,etc]
# bosses = [boss1, boss2]


# ================================================ Game loop setup ==========================================================================================================================================

bullet_list = [] 
bosses = []
particles = []

# Screen Shake Variables
shake_timer = 0
world_surface = pygame.Surface((WIDTH, HEIGHT))

#Debugging
show_hitbox = False
show_player_hitbox = False
show_bullet_hitbox = False
show_atk_hitbox = True
show_img_rect = False

clock = pygame.time.Clock()
running = True
action = 0
click_pos = None


# ================================================ Game loop ==========================================================================================================================================

while running: 
    # dt = clock.tick(60) / 1000  # .tick(framerate) mengembalikan waktu ms antar frame, ms / 1000 = detik

    og_dt = clock.tick(60) / 1000  #slow mo effect when overloaded, use when having too much frame drops
    og_dt = min(og_dt, 0.033)  # cap at ~30 FPS equivalent
    
    fps = clock.get_fps() 
    # scale += ((Target scale) - cur_scale) * 5 * dt for smooth time scale transition
    time_scale = 1.0
    if fps < 55: time_scale += (fps / 60 - time_scale) * 5 * og_dt
    else: time_scale += (1.0 - time_scale) * 5 * og_dt

    target_dt = 1 / 60  # use this or below?
    dt = target_dt * time_scale
    
    keys = pygame.key.get_pressed()
    action = 0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: 
                action = 1 #mouse leftclick
                click_pos = event.pos 
            if event.button == 3: action = 3 #mouse rightclick 
        if event.type == pygame.MOUSEBUTTONUP:
            action = 0

    # Update Entities
    PlayerTest.update(keys, dt, Platform_list)
    action = 0 #reset action

    for b in bosses:
        b.update(dt, PlayerTest, bullet_list)

        for hitbox in PlayerTest.attack_hitboxes_active:
            if b and b.hp > 0 and hitbox.colliderect(b.rect):
                if not b.grace_active:
                    PlayerTest.action_cd_timer = max(0 , PlayerTest.action_cd_timer - PlayerTest.attack_cd/5) # lower cd if succesful attack
                    b.take_damage()
                    b.grace_time = pygame.time.get_ticks()
                    b.grace_active = True
        
    for p in particles[:]:
        p.update(dt)
        if p.lifetime <= 0:
            particles.remove(p)
    
    # show_hitbox = True if len(bullet_list) > 20 else False
    for projectile in bullet_list[:]:
        projectile.update(dt)

        #Check i-frame & kolisi
        current_radius = PlayerTest.hitbox_radius + (PlayerTest.absorb_radius if PlayerTest.absorb_active else 0) 
        if circle_collide(PlayerTest.rect.center, current_radius, projectile.rect.center, projectile.hitbox_radius):
            # Absorb
            if PlayerTest.absorb_active and not PlayerTest.is_phasing: 
                if bullet_list: bullet_list.remove(projectile)
                PlayerTest.phase_bar = min(2 , PlayerTest.phase_bar + 0.3)
                PlayerTest.action_cd_timer = max(0 , PlayerTest.action_cd_timer - PlayerTest.absorb_cd/3) # Lower cd if parried
                spawn_particles(projectile.rect.centerx, projectile.rect.centery, CYAN2_0, 6) # Absorb Sparks
                PlayerTest.absorb_count += 1
                if PlayerTest.absorb_count >= 5:
                    PlayerTest.hp = min(PlayerTest.hp + 1, PlayerTest.max_hp)
                    PlayerTest.absorb_count = 0
                    spawn_particles(PlayerTest.rect.centerx, PlayerTest.rect.centery, GREEN, 15) # Heal Sparks
                continue
            
            # Got hit
            if not PlayerTest.is_phasing and not PlayerTest.grace_active: #grace_active = grace active or not
                bullet_list.clear()
                PlayerTest.hp -= 1
                PlayerTest.grace_time = pygame.time.get_ticks()
                PlayerTest.grace_active = True
                shake_timer = 0.25 # Trigger Screen Shake
                spawn_particles(PlayerTest.rect.centerx, PlayerTest.rect.centery, RED2_0, 10)
                if PlayerTest.hp <= 0:
                    print("GAME OVER") # will make a retry/quit button
                    #running = False
                continue
    
        if projectile.out_of_bounds():
            if bullet_list: bullet_list.remove(projectile)
            continue
    
    if shake_timer > 0:
        shake_timer -= dt

    
    # Draw objects 
    world_surface.blit(background_image, (0,0))
    
    for platform in Platform_list:
        if show_hitbox: pygame.draw.rect(world_surface, BROWN, platform.rect) #hitbox
        platform.draw_self(world_surface)
    
    for projectile in bullet_list:
        projectile.draw_self(world_surface)
        if show_bullet_hitbox: projectile.draw_hitcircle(world_surface, RED)

    for b in bosses:
        b.draw(world_surface)
        if show_hitbox: pygame.draw.rect(world_surface, RED, b.rect, 2) # boss hitbox
    
    PlayerTest.draw(world_surface)
    if show_player_hitbox: PlayerTest.draw_hitcircle(world_surface, color=YELLOW, hitbox_radius=PlayerTest.hitbox_radius, border_width=3)
       
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
    draw_ui(screen, PlayerTest, bosses)

    pygame.display.update()

pygame.quit()
sys.exit()
