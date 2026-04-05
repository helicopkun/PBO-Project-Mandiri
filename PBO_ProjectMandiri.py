import pygame
import sys
import random
import math

pygame.init()
pygame.font.init()

WIDTH = 1920
HEIGHT = 1080
GROUND_Y = HEIGHT - 250

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
               size_offsetx = 0, size_offsety = 0): # offset for minor adjustment, not needed if image is edited on figma
    scale = None
    if rect: 
        scale = (rect.width + size_offsetx, rect.height + size_offsety) #size based on rect
    elif size_offsetx or size_offsety: 
        scale = (size_offsetx, size_offsety) # size only

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
    def __init__ (self, x, y, width = 20, height = 20, hitbox_radius = 15, 
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

class Player(GameObject):
    def __init__(self, max_hp=5, name = "Baka", image = "cirno.png", attack = 'slash'):
        super().__init__(x= 50, y=GROUND_Y-50, width=50, height=100, hitbox_radius=15,
                         image_path="character/"+image, size_offsetx=70, size_offsety=30)
        # If value = None, 0, T|F, Rect, string  -> will be used as referenced var, 
        # else -> only for character stats (for easier scaling), duration is scaled on seconds
        
        # elapsed -> stopwatch (0,1,2, until n) counting up <-> threshold
        # timestamp -> records the time an action triggered <-> duration
        # remaining -> timer (n, n-1, 0) counting down

        self.name = name
        self.sizeHitbox = self.hitbox_radius
        self.speedX = 400
        self.speedY = 400
        self.gravity = 350

        self.max_hp = max_hp
        self.hp = self.max_hp
        self.absorb_count = 0 

        self.grace_active = False # i-frame setelah kena hit
        self.grace_duration = 1.5
        self.grace_timestamp = 0

        self.is_phasing = False
        self.phase_speed = 1.5

        self.phase_bar = 0 # current bar
        self.phase_barMax = 2 #sekon
        self.phase_barRate = 0.5 #bar recharge per second
        self.phase_barCD_duration = 0.6 #cooldown before recharge
        self.phase_barCD_timestamp = 0

        self.is_jumping = False
        self.jump_duration_threshold = 0.4 # jump duration
        self.jump_duration_elapsed = 0                    
        self.jump_recovery_threshold = 0.15 # jump cooldown 
        self.jump_recovery_elapsed = 0
        self.airborne_threshold = 0.1 # airborne duration 
        self.airborne_elapsed = 0
        self.current_platform = None
        self.platform_group = None
        self.quickfall_plat_threshold = 0.225
        self.quickfall_plat_elapsed = 0
        self.old_bottom = self.rect.bottom
        
        self.action_cd_remaining = 0 # action cooldown
        self.action_cd_barMax = 1.3

        self.absorb_active = False
        self.absorb_duration = 0.3  # Window absorb
        self.absorb_cd = 1
        self.absorb_radius = 30
        self.absorb_color = CYAN

        self.facing = 'right'
        self.facing_angle = 0
        self.facing_right = True
        self.look_attack_timestamp = 0
        self.look_jump_timestamp = 0
        
        self.attack_type = attack
        self.attack_type_data = attack_type[attack]
        self.active_attacks = []
        self.copy_rect = None #copying self old pos
          
    def update(self, keys, click_state, dt, platforms):
        self.platform_group = platforms
        
        # Movement - freeze when absorbing
        if not self.absorb_active:
            self.move(keys, dt) 
        
        self.current_state()

        self.facing_indicator(keys, click_state)
        self.bar_indicator()
        
        # Actions
        if not (self.is_phasing or self.action_cd_remaining > 0 or self.grace_active):
            self.actions(keys, click_state)
                
    def draw(self, surface):
        #Character
        self.image = get_image(image_path=self.image_path, flipx=0 if self.facing_right else 1, rect=self.rect, 
                                                                                            size_offsetx=70, 
                                                                                            size_offsety=30)
        if not (self.grace_active and pygame.time.get_ticks() % 200 < 100): #efek kedip saat kena hit
            self.draw_self(surface)

        if self.absorb_active:
            pygame.draw.circle(surface, self.absorb_color, self.rect.center, self.hitbox_radius + self.absorb_radius, 5)

        for atk in self.active_attacks:
            atk_type = atk['type_data']
            if atk['cur_frame'] < atk_type['frame_count']:
                current_img = atk['images'][atk['cur_frame']]
                atk_img_rect = current_img.get_rect(center=(atk['center']))
                surface.blit(current_img, atk_img_rect)
                if show_atk_hitbox:
                    for hitbox in atk['hitboxes']:
                        pygame.draw.rect(surface, YELLOW, hitbox, 2)
                    for hitbox in atk['active_hitboxes']:
                        pygame.draw.rect(surface, RED2_0, hitbox, 2)

                frame_delay = (atk_type['duration']*1000) / atk_type['frame_count'] # i put it here so frame 0 can still play
                if pygame.time.get_ticks() - atk['frame_timestamp'] > frame_delay:
                    atk['frame_timestamp'] = pygame.time.get_ticks()
                    atk['cur_frame'] += 1            
            else:
                self.active_attacks.remove(atk)
            
        if self.action_cd_remaining > 0:
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

    def take_damage(self):
        self.hp -= 1
        self.grace_timestamp = pygame.time.get_ticks()
        self.grace_active = True
        spawn_particles(self.rect.centerx, self.rect.centery, RED2_0, 10)

    def actions(self, keys, click_state):
        #Absorb
        if (keys[pygame.K_l] or click_state['right']):                                            
            self.absorb_active = True
            self.absorb_timer = self.absorb_duration
            self.action_cd_remaining = self.absorb_cd
            
        #Attack
        if (keys[pygame.K_k] or click_state['left']):
            self.look_attack_timestamp = pygame.time.get_ticks()
            self.action_cd_remaining = self.attack_type_data['cd']
            attack_images = [] #get image and reset if it existed
            offset_dist = 300
            angle = math.radians(self.facing_angle)
            for i in range(self.attack_type_data['frame_count']):
                attack_images.append(get_image(f"attack/{self.attack_type}/{self.attack_type}-{i}.png", 
                                                    angle=self.facing_angle))
            atk_image_center = ( # get setup pos (static pos)
                self.rect.centerx + math.cos(angle) * offset_dist,
                self.rect.centery + math.sin(-angle) * offset_dist
            )
            self.copy_rect = self.rect.copy()
            base_hitboxes = self.generate_attack_hitbox() # pathway for active hitbox
            new_attack = { # get data for attack
                'type': self.attack_type,
                'type_data': self.attack_type_data,
                'images': attack_images,
                'center': atk_image_center,
                'hitboxes': base_hitboxes,
                'active_hitboxes': [],
                'target': {}, # add enemy: tick, enemy for checking 
                'cur_frame': 0,
                'frame_timestamp': 0
            }   
            self.active_attacks.append(new_attack)

    def absorbed(self, bullet): #succesful absorb
        self.phase_bar = min(2 , self.phase_bar + 0.3)
        self.action_cd_remaining = max(0 , self.action_cd_remaining - self.absorb_cd/3) # Lower cd if parried
        spawn_particles(bullet.rect.centerx, bullet.rect.centery, CYAN2_0, 6) # Absorb Sparks
        self.absorb_count += 1
        if self.absorb_count >= 5:
            self.hp = min(self.hp + 1, self.max_hp)
            self.absorb_count = 0
            spawn_particles(self.rect.centerx, self.rect.centery, GREEN, 15) # Heal Sparks

    def attacked(self, enemy, atk): #succesful attack, atk = general data of attack , atk_type = specific (slash, pierce, etc..)
        if enemy.hp <= 0 or enemy.grace_active:
            return
        
        atk_type = atk['type_data']
        
        if atk_type['damage_tick'] == 'single': # hit once after colision
            if enemy in atk['target']:
                return 
            atk['target'][enemy] = -1 #just assign random integer 
            self.action_cd_remaining = max(0 , self.action_cd_remaining - atk_type['cd']/5) # lower cd if succesful single-hit attack


        tick = 0.15
        if atk_type['damage_tick'] == 'multi': # hit every tick-rate per colision
            if enemy in atk['target'] and atk['target'][enemy] > 0:
                return
            atk['target'][enemy] = tick
        
        enemy.take_damage(atk_type['damage'])

    def on_platform(self):
        for platform in self.platform_group:
            if self.rect.right > platform.rect.left and self.rect.left < platform.rect.right: # ketika ujung player memasuki area platform
                if self.rect.bottom >= platform.rect.top and self.old_bottom <= platform.rect.top + 5:
                    self.current_platform = platform
                    return True
        self.current_platform = None
        return False
    
    def move(self, keys, dt):
        on_plat = self.on_platform() #cache on_plat if dont need to check all the time
        self.old_bottom = self.rect.bottom # save old footing
            
        #Phasing movement
        if keys[pygame.K_LSHIFT] and self.action_cd_remaining <= 0 and not self.grace_active:
            if self.phase_bar > 0:
                self.phase_bar -= dt
                self.hitbox_radius = 0
                self.is_phasing = True 
            else:
                self.is_phasing = False
            self.phase_barCD_timestamp = pygame.time.get_ticks()  # set CD after phasing

        else:
            if pygame.time.get_ticks() - self.phase_barCD_timestamp >= self.phase_barCD_duration * 1000: # Recharge after CD
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
            self.rect.bottom = min(GROUND_Y, self.rect.bottom)
            
            return #agar tidak double dari movement biasa 

        #Horizontal movement
        if keys[pygame.K_a]:
                self.rect.centerx -= self.speedX * dt
                self.rect.left = max(0, self.rect.left)

        if keys[pygame.K_d]:
                self.rect.centerx += self.speedX * dt
                self.rect.right = min(WIDTH, self.rect.right)

        #Vertical movement
        if keys[pygame.K_s]:
            allow_quickfall = self.quickfall_plat_elapsed >= self.quickfall_plat_threshold
            self.rect.centery += self.speedY * dt

            if self.on_platform() and not allow_quickfall: #use function because need to always check (input and cache delay shenanigans)
                self.rect.bottom = self.current_platform.rect.top #clamp to cur plat
            else:
                self.rect.bottom = min(GROUND_Y, self.rect.bottom)

        if keys[pygame.K_s] and self.on_platform(): self.quickfall_plat_elapsed += dt #delay quickfall between platform
        else :                                      self.quickfall_plat_elapsed = 0

        if keys[pygame.K_w] and on_plat and not self.is_jumping:
            if self.jump_recovery_elapsed >= self.jump_recovery_threshold:
                self.is_jumping = True                  
                self.jump_duration_elapsed = 0
                self.jump_recovery_elapsed = 0
        
        if self.is_jumping:
            if keys[pygame.K_w] and not keys[pygame.K_s] and self.jump_duration_elapsed < self.jump_duration_threshold:  # Durasi lompat jika di tahan -> sampai max                            
                self.rect.centery -= self.speedY * dt
                self.rect.top = max(0, self.rect.top)
                self.jump_duration_elapsed += dt
            else: # Jika w berhenti ditahan, quick-fall, mencapai batas max = sudah tidak jumping
                self.is_jumping = False

        #Reset airborne, cooldown jump, etc jika berada di platform
        if self.on_platform() and not (self.is_jumping):
            self.jump_recovery_elapsed += dt
            self.airborne_elapsed = 0
                 
        #Gravitasi
        if not (self.on_platform() or self.is_jumping):
            self.airborne_elapsed += dt # set airborne
            if self.airborne_elapsed > self.airborne_threshold: #stop airborne if airborne_elapsed = max
                slowing = self.gravity/2 if keys[pygame.K_w] else 0 
                self.rect.centery += (self.gravity - slowing) * dt
                self.rect.bottom = min(GROUND_Y, self.rect.bottom)

    def facing_indicator(self, keys, click_state):
        #Movement facing indicator
        if not self.absorb_active:
            if pygame.time.get_ticks() - self.look_attack_timestamp >= 400: # only works after for when just launching attack
                
                if keys[pygame.K_w]: # set delay timer after look up (or down too? if i wanna)
                    self.look_jump_timestamp = pygame.time.get_ticks()
                        
                if keys[pygame.K_d] and not keys[pygame.K_a]: self.facing_right = True 
                if keys[pygame.K_a] and not keys[pygame.K_d]: self.facing_right = False

                if keys[pygame.K_w] and not keys[pygame.K_s]: self.facing = 'up'
                if keys[pygame.K_s] and not keys[pygame.K_w]: self.facing = 'down'

                if self.facing == 'up': 
                    if keys[pygame.K_d] and not keys[pygame.K_a]: self.facing = 'top-right'
                    if keys[pygame.K_a] and not keys[pygame.K_d]: self.facing = 'top-left'

                if self.facing == 'down':
                    if keys[pygame.K_d] and not keys[pygame.K_a]: self.facing = 'bottom-right'
                    if keys[pygame.K_a] and not keys[pygame.K_d]: self.facing = 'bottom-left'
                
                if pygame.time.get_ticks() - self.look_jump_timestamp >= 200: # delay after jump
                    self.facing = 'right' if self.facing_right else 'left'
                
        # Attack facing indicator
        if self.action_cd_remaining <= 0:
            direction = ['right', 'top-right', 'up', 'top-left', 'left', 'bottom-left', 'down', 'bottom-right']
            if click_state['left']:
                mx , my = click_state['pos']
                dx = mx - self.rect.centerx
                dy = my - self.rect.centery

                self.facing_angle = math.degrees(math.atan2(-dy, dx)) #-dy because pygame y is flipped
                # shifts from 0 <-> 44 to -22.5 <-> 22.5 for index 0      
                index = int((self.facing_angle + 22.5) // 45) % 8 # 22.5 for shifting angle, e.g: without 0 - 44 -> 0 instead turn into (-22.5 + 22.5) to (22.5 + 22.5) -> 0
                self.facing = direction[index] # convert 24-d to 8-d
                
                self.facing_angle = round(self.facing_angle / 15) * 15 # snap to 15*

                # Reset facing after different direction from current direction attack
                if self.facing in {'right', 'top-right', 'bottom-right'}:
                    self.facing_right = True
                if self.facing in {'left', 'top-left', 'bottom-left'}: 
                    self.facing_right = False

            elif keys[pygame.K_k]:
                for i in range(8):
                    if self.facing == direction[i]:
                        self.facing_angle = i * 45

        # Char facing for direction
        if self.facing in {'right', 'top-right', 'bottom-right'}: self.facing_right = True
        if self.facing in {'left', 'top-left', 'bottom-left'}: self.facing_right = False

    def current_state(self): #Update cooldown, grace, duration
        #Check phasing for hitbox radius
        if self.is_phasing: self.hitbox_radius = 0
        else: self.hitbox_radius = self.sizeHitbox
        
        #Hit Grace      
        if self.grace_active and pygame.time.get_ticks() - self.grace_timestamp >= self.grace_duration * 1000:
            self.grace_active = False
        
        #Action CD, cannot different action at same time, different CD based on last action
        if self.action_cd_remaining > 0:
            self.action_cd_remaining -= dt

        # Absorb duration
        if self.absorb_active:
            self.absorb_timer -= dt
            if self.absorb_timer <= 0:
                self.absorb_active = False

        # Attack
        for atk in reversed(self.active_attacks): # read in reverse for safely removing atk
            self.attacking(atk)

    def attacking(self, atk): #generate active frame hitbox for specific attack
        atk['active_hitboxes'].clear()# Reset active hitboxes every frame
        start_frame = atk['type_data']['active_frames'][0]
        end_frame = atk['type_data']['active_frames'][1]

        if start_frame <= atk['cur_frame'] <= end_frame: #check if in the active frame window
            total_active_frames = max(1, end_frame - start_frame) # prevent division by zero
            progress = (atk['cur_frame'] - start_frame) / total_active_frames
            total_hitboxes = len(atk['hitboxes'])

            if atk['type'] == 'slash': # --- THE SWEEP LOGIC --- Visual: {}{}[>][>]{}{} -> Sweeps across the chain
                current_tip = int(progress * total_hitboxes) + 3
                hitbox_length = 4 
                start_idx = max(0, current_tip - hitbox_length) # hitbox tail
                atk['active_hitboxes'] = atk['hitboxes'][start_idx : current_tip]

            elif atk['type'] == 'pierce': # --- THE GROW LOGIC --- Visual: [>][>][>]{}{} -> Grows from base to tip
                current_tip = int(progress * total_hitboxes) + 1
                atk['active_hitboxes'] = atk['hitboxes'][:current_tip]
            
            else: # Default fallback (Spin / All at once)
                atk['active_hitboxes'] = atk['hitboxes'].copy()
            
    def generate_attack_hitbox(self): # generate chain hitbox trajectory, not needing atk data because only load ONCE during the trigger phase
        n = 10  # more = smoother coverage

        if self.attack_type == 'slash':
            length = 2 * self.height
            thickness = self.width
        if self.attack_type == 'pierce': 
            length = 4 * self.height
            thickness = self.width

        length *= self.attack_type_data['scale']
        thickness *= self.attack_type_data['scale']

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
                                        self.rect.height / 2 * self.action_cd_barMax)
        self.action_bar_rectMax.centerx = (self.rect.right + 20) if not self.facing_right else (self.rect.left - 20) #kebalikan facing
        self.action_bar_rectMax.centery = self.rect.centery
        
        self.action_bar_rect = pygame.Rect(0, 0, self.action_bar_rectMax.width, 
                                        self.rect.height / 2 * (self.action_cd_barMax - self.action_cd_remaining))
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
        self.hit_tick = 0
        self.grace_active = False
        self.grace_timestamp = 0
        self.grace_duration = 200
        self.alive = True

        self.base_y = float(start_y)
        self.bop_amplitude = 25
        self.bop_frequency = 3

        self.direction = direction # 1 for right, -1 for left
        self.fire_timer = 0
        
    def update(self, dt, player, bullet_list):
        if not self.alive: return
        
        if self.hit_tick > 0: self.hit_tick -= dt

        if self.grace_active and pygame.time.get_ticks() - self.grace_timestamp >= self.grace_duration:
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
            if pygame.time.get_ticks() - player.grace_timestamp >= 1000: #delay after player get hit & first spawn
                self.shoot(player, bullet_list, phase)
            
    def draw(self, surface):
        if not self.alive: return
        color = self.phases[self.current_phase]['color']
        if not (self.grace_active and pygame.time.get_ticks() % 200 < 100): #efek kedip saat kena hit
            self.draw_hitcircle(surface, color, 6) #draw hitbox here is more like indicator in the middle, color for phase color
            self.draw_hitcircle(surface, self.circle_color, 10, 3) #self.color for boss main color
            self.draw_self(surface)
   
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
                    cy = random.randint(0, GROUND_Y)
                    bx = random.uniform(-300, -150) 
                    by = random.uniform(-50, 50)
                else: # left # Move right
                    cx = -20
                    cy = random.randint(0, GROUND_Y)
                    bx = random.uniform(150, 300) 
                    by = random.uniform(-50, 50)
                angle = -math.degrees(math.atan2(by, bx))
                angle = round(angle / 5) * 5
                bullet_list.append(Bullet(cx, cy, bx, by, size, color, image, angle=angle))
                
    def take_damage(self, atk_dmg):
        self.hp -= atk_dmg
        self.grace_timestamp = pygame.time.get_ticks()
        self.grace_active = True
        spawn_particles(self.rect.centerx, self.rect.centery, color=RED2_0, count=10) # Hit feedback
        if self.hp <= 0:
            self.current_phase += 1
            self.change_phase()
            
    def change_phase(self):
        spawn_particles(self.rect.centerx, self.rect.centery, color=RED, count=30, is_burst=True) # Trigger massive death particle burst each transition 
        if self.current_phase > self.total_phases:
            self.alive = False
            spawn_particles(self.rect.centerx, self.rect.centery, color=RED2_0, count=50, is_burst=True)
        else:
            self.max_hp = self.phases[self.current_phase]['max_hp']
            self.hp = self.max_hp
          
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
        return self.rect.right < -50 or self.rect.left > WIDTH + 50 or self.rect.top > HEIGHT or self.rect.bottom < -50

#VFX
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
        cur_stage = self.stages_data[self.stage_counter]

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

        if cur_stage['bosses'] == 'random': 
            self.boss_list = self.generate_random_boss()
        else: 
            self.boss_list = cur_stage['bosses']
        
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
        circle_color_list = [RED, GREEN, YELLOW, BLACK, WHITE]
        boss_list = []
        for i in range(random.randint(1,3)): #generate 3 boss, 3 is already too much man
            size = random.randint(100, 200)
            start_x = random.uniform(100, WIDTH - 100)
            direction=random.choice([1 , -1])
            circle_color = random.choice(circle_color_list)
            boss = Boss(f"Boss {i+1}", self.generate_boss_phase(), size, size, start_x, direction, circle_color)
            circle_color_list.remove(circle_color)
            boss_list.append(boss)
        return boss_list

# ================================================ Enemy making - manual ==========================================================================================================================================

# Enemy making - color for phase color - bullet image = 'asset/ + {bullet-orb, bullet-1, bullet-2, bullet-3} + .png'
boss1_phase = { 
            1: {'max_hp': 15, 'move_speed': 100, 'y_axis': 150, 'rate': 1.5, 'pattern': 'circle', 
                'num_bullet': 5, 'bullet_spd': 300, 'bullet_size': 10,'color': ORANGE, 'image': 'bullet-1'},

            2: {'max_hp': 18, 'move_speed': 200, 'y_axis': 250, 'rate': 2, 'pattern': 'random', 
                'num_bullet': 5, 'bullet_spd': 350, 'bullet_size': 8,'color': PURPLE, 'image': 'bullet-3'},

            3: {'max_hp': 16, 'move_speed': 250, 'y_axis': 350, 'rate': 1.0, 'pattern': 'circle', 
                'num_bullet': 8, 'bullet_spd': 400, 'bullet_size': 15,'color': BLUE, 'image': 'bullet-2'},

            4: {'max_hp': 14, 'move_speed': 100, 'y_axis': 400, 'rate': 0.8, 'pattern': 'fan', 
                'num_bullet': 7, 'bullet_spd': 400, 'bullet_size': 7,'color': CYAN, 'image': 'bullet-2'},

            5: {'max_hp': 13, 'move_speed': 550, 'y_axis': 150, 'rate': 0.4, 'pattern': 'chaos', 
                'num_bullet': 8, 'bullet_spd': 450, 'bullet_size': 9,'color': GOLD, 'image': 'bullet-orb'}
        }
boss2_phase = { 
            1: {'max_hp': 16, 'move_speed': 350, 'y_axis': 200, 'rate': 0.8, 'pattern': 'chaos', 
                'num_bullet': 4, 'bullet_spd': 400, 'bullet_size': 8, 'color': ORANGE, 'image': 'bullet-3'},

            2: {'max_hp': 18, 'move_speed': 100, 'y_axis': 450, 'rate': 0.5, 'pattern': 'random', 
                'num_bullet': 3, 'bullet_spd': 300, 'bullet_size': 12, 'color': PURPLE, 'image': 'bullet-1'},

            3: {'max_hp': 20, 'move_speed': 400, 'y_axis': 150, 'rate': 1.2, 'pattern': 'circle', 
                'num_bullet': 16, 'bullet_spd': 250, 'bullet_size': 6, 'color': BLUE, 'image': 'bullet-3'},

            4: {'max_hp': 17, 'move_speed': 600, 'y_axis': 300, 'rate': 0.4, 'pattern': 'random', 
                'num_bullet': 5, 'bullet_spd': 500, 'bullet_size': 7, 'color': CYAN, 'image': 'bullet-1'},

            5: {'max_hp': 22, 'move_speed': 700, 'y_axis': 200, 'rate': 0.2, 'pattern': 'chaos', 
                'num_bullet': 10, 'bullet_spd': 450, 'bullet_size': 10, 'color': GOLD, 'image': 'bullet-1'}
        }

boss1 = Boss("Cubecicle", boss2_phase, w=100, h=100, start_x=random.uniform(100, WIDTH - 100), direction=random.choice([1 , -1]), circle_color=CYAN)
boss2 = Boss("And more..", boss1_phase, w=140, h=140, start_x=random.uniform(100, WIDTH - 100), direction=random.choice([1 , -1]), circle_color=CYAN2_0)




# ================================================ Stage making ==========================================================================================================================================

STAGES_ICY = {
    1: {
        "bosses": [boss1], 
        "bg": "icy_cave.png",
        "platforms": [[150,250], [450,400], [700,100], [1100, 100], [1300,400], [1600,250]],
        "plat_img": "platform.png",
        "main_plat_img": "mainplatform.png",
        "music": "ice_theme.mp3"
    },
    2: {
        "bosses": [boss1, boss2], 
        "bg": "icy_cave.png",
        "platforms": [[150,250], [450,400], [700,100], [1100, 100], [1300,400], [1600,250]],
        "plat_img": "platform.png",
        "main_plat_img": "mainplatform.png",
        "music": "ice_theme.mp3"
    },
}

bg = "icy_cave"
background_image = pygame.image.load('assets/background/' + bg + '.png')
background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))

MainPlatform = GameObject(WIDTH//2, HEIGHT, WIDTH, 250, size_offsetx=200, image_path="platform/mainplatform.png",
                                                        size_offsety=1000)

MainPlatform.rect.top = GROUND_Y


# ================================================ Player making ==========================================================================================================================================

attack_type = {
            "slash":    {'damage': 2.5, 'damage_tick': 'single', 'duration': 0.3, 'active_frames': (2, 8), 'frame_count': 10, 'cd': 0.8, 'scale':3},
            "pierce":   {'damage': 3.0, 'damage_tick': 'single', 'duration': 0.50, 'active_frames': (4, 8), 'frame_count': 9, 'cd': 1.2, 'scale':3},
            "spin" :    {'damage': 0.5, 'damage_tick': 'multi','duration': 0.70, 'active_frames': (2, 10),'frame_count': 13,'cd': 1.0, 'scale':3},
        }

PlayerTest = Player(max_hp=15, name="HelicopKun", attack='slash')
#might do hotbar inventory-based attacks 1.slash, 2.Pierce, 3...


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
    for b in reversed(boss_list): #read in reverse, so boss1 on top of boss2
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
particles = []

# ================================================ Game loop setup ==========================================================================================================================================


stage = StageManager(STAGES_ICY)
stage.load_stage()

# Screen Shake Variables
shake_timer = 0
world_surface = pygame.Surface((WIDTH, HEIGHT))

#Debugging
show_hitbox = False
show_player_hitbox = False
show_bullet_hitbox = False
show_atk_hitbox = False
show_img_rect = False

clock = pygame.time.Clock()
# time_scale = 1.0

running = True
# ================================================ Game loop ==========================================================================================================================================

while running: 
    dt = clock.tick(60) / 1000  # .tick(framerate) mengembalikan waktu ms antar frame, ms / 1000 = detik

    # og_dt = clock.tick(60) / 1000  #slow-mo effect when overloaded, use when having too much frame drops
    # og_dt = min(og_dt, 0.033)  # cap at ~30 FPS equivalent
    
    # fps = clock.get_fps() 
    # if fps < 55: time_scale += (fps / 60 - time_scale) * 5 * og_dt
    # else: time_scale += (1.0 - time_scale) * 5 * og_dt
    # time_scale = max(0.5, min(time_scale, 1.2))

    # target_dt = 1 / 60
    # dt = target_dt * time_scale
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False


    keys = pygame.key.get_pressed()

    click_state = {
        'left': False,
        'right': False,
        'pos': None
    }

    mouse_buttons = pygame.mouse.get_pressed()
    mouse_pos = pygame.mouse.get_pos()

    click_state['left'] = mouse_buttons[0]
    click_state['right'] = mouse_buttons[2]
    click_state['pos'] = mouse_pos
        

    # Update Entities
    PlayerTest.update(keys, click_state, dt, stage.plat_list)

    for b in stage.boss_list:
        b.update(dt, PlayerTest, stage.bullet_list)

        for atk in PlayerTest.active_attacks:
            for hitbox in atk['active_hitboxes']:
                if hitbox.colliderect(b.rect):
                    PlayerTest.attacked(b, atk)

            for enemy in list(atk['target']): #reduce tick_rate cd 
                if atk['target'][enemy] > 0:
                    atk['target'][enemy] -= dt    
                    
                        
    for p in particles[:]: #safely remove with copying list
        p.update(dt)
        if p.lifetime <= 0:
            particles.remove(p)
    
    # show_hitbox = True if len(bullet_list) > 20 else False 
    for bullet in stage.bullet_list[:]: #safely remove with copying list
        bullet.update(dt)

        if bullet.out_of_bounds():
            if stage.bullet_list: stage.bullet_list.remove(bullet)
            continue

        #Check i-frame & kolisi player
        current_radius = PlayerTest.hitbox_radius + (PlayerTest.absorb_radius if PlayerTest.absorb_active else 0) 
        if circle_collide(PlayerTest.rect.center, current_radius, bullet.rect.center, bullet.hitbox_radius):
            # Absorb
            if PlayerTest.absorb_active and not PlayerTest.is_phasing: 
                PlayerTest.absorbed(bullet)
                if stage.bullet_list: stage.bullet_list.remove(bullet)
                continue
            
            # Got hit
            if not PlayerTest.is_phasing and not PlayerTest.grace_active: #grace_active = grace active or not
                PlayerTest.take_damage()
                stage.bullet_list.clear() #remove all bullet
                shake_timer = 0.25 # Trigger Screen Shake
                if PlayerTest.hp <= 0:
                    print("GAME OVER") # will make a retry/quit button
                    #running = False
                continue
    
    if shake_timer > 0:
        shake_timer -= dt

    
    # Draw objects 
    world_surface.blit(background_image, (0,0))
    
    for platform in stage.plat_list:
        if show_hitbox: pygame.draw.rect(world_surface, BROWN, platform.rect) #hitbox
        platform.draw_self(world_surface)
    
    PlayerTest.draw(world_surface)
    if show_player_hitbox: PlayerTest.draw_hitcircle(world_surface, color=YELLOW, hitbox_radius=PlayerTest.hitbox_radius, border_width=3)

    for bullet in stage.bullet_list:
        bullet.draw_self(world_surface)
        if show_bullet_hitbox: bullet.draw_hitcircle(world_surface, RED)

    for b in stage.boss_list:
        b.draw(world_surface)
        if show_hitbox: pygame.draw.rect(world_surface, RED, b.rect, 2) # boss hitbox
       
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
    draw_ui(screen, PlayerTest, stage.boss_list)

    pygame.display.update()

pygame.quit()
sys.exit()
