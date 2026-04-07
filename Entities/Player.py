import pygame, math
from Entities.GameObject import GameObject
from Entities.Particle import spawn_particles
from Shared.constants import*
from Shared.utils import load_json, get_end_pos, get_image

class Player(GameObject):
    def __init__(self, name = "Baka", image = "cirno.png", attack = 'slash'):
        self.config = load_json("player/config.json")
        attack_data = load_json("player/attack.json")

        super().__init__(x= 50, y=GROUND_Y-50, width=50, height=100, hitbox_radius=self.config['hitbox'],
                         image_path="character/"+image, size_offsetx=70, size_offsety=30)

        # elapsed -> stopwatch (0,1,2, until n) counting up <-> threshold
        # timestamp -> records the time an action triggered <-> duration
        # remaining -> timer (n, n-1, 0) counting down
        
        self.name = name
        self.cur_hitbox = self.hitbox_radius

        self.max_hp = self.config['max_hp']
        self.hp = self.max_hp
        self.absorb_count = 0 

        self.grace_active = False # i-frame setelah kena hit
        self.grace_timestamp = 0

        self.is_phasing = False
        self.phase_bar = 0 # current bar
        self.phase_barCD_timestamp = 0

        self.is_jumping = False
        self.jump_duration_elapsed = 0
        self.jump_recovery_elapsed = 0
        self.airborne_elapsed = 0

        self.current_platform = None
        self.platform_group = None
        self.quickfall_plat_elapsed = 0
        self.old_bottom = self.rect.bottom
        
        self.action_cd_remaining = 0 # action cooldown

        self.absorb_radius = self.config['absorb_radius']
        self.absorb_active = False
        self.absorb_color = CYAN
        
        self.attack_type = attack
        self.attack_type_data = attack_data[attack]
        self.active_attacks = []
        self.copy_rect = None #copying self old pos
        
        self.facing = 'right'
        self.facing_angle = 0
        self.facing_right = True
        self.look_attack_timestamp = 0
        self.look_jump_timestamp = 0

    def update(self, keys, click_state, dt, platforms):
        self.platform_group = platforms
        
        # Movement - freeze when absorbing
        if not self.absorb_active:
            self.move(keys, dt) 
        
        self.current_state(dt)

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

        if self.phase_bar < self.config['phase_max']:
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
            self.absorb_timer = self.config['absorb_duration']
            self.action_cd_remaining = self.config['absorb_cd']
            
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
        self.action_cd_remaining = max(0 , self.action_cd_remaining - self.config['absorb_cd']/3) # Lower cd if parried
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
            if pygame.time.get_ticks() - self.phase_barCD_timestamp >= self.config['phase_cd_delay'] * 1000: # Recharge after CD
                self.phase_bar = min(self.config['phase_max'], self.phase_bar + self.config['phase_rate'] * dt)
            
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
        
            self.rect.centerx += dx * self.config['speedX'] * dt * self.config['phase_spd']
            self.rect.left = max(0, self.rect.left)
            self.rect.right = min(WIDTH, self.rect.right)
            
            self.rect.centery += dy * self.config['speedY'] * dt * self.config['phase_spd']
            self.rect.top = max(0, self.rect.top)
            self.rect.bottom = min(GROUND_Y, self.rect.bottom)
            
            return #agar tidak double dari movement biasa 

        #Horizontal movement
        if keys[pygame.K_a]:
                self.rect.centerx -= self.config['speedX'] * dt
                self.rect.left = max(0, self.rect.left)

        if keys[pygame.K_d]:
                self.rect.centerx += self.config['speedX'] * dt
                self.rect.right = min(WIDTH, self.rect.right)

        #Vertical movement
        if keys[pygame.K_s]:
            allow_quickfall = self.quickfall_plat_elapsed >= self.config['quickfall_plat_threshold']
            self.rect.centery += self.config['speedY'] * dt

            if self.on_platform() and not allow_quickfall: #use function because need to always check (input and cache delay shenanigans)
                self.rect.bottom = self.current_platform.rect.top #clamp to cur plat
            else:
                self.rect.bottom = min(GROUND_Y, self.rect.bottom)

        if keys[pygame.K_s] and self.on_platform(): self.quickfall_plat_elapsed += dt #delay quickfall between platform
        else :                                      self.quickfall_plat_elapsed = 0

        if keys[pygame.K_w] and on_plat and not self.is_jumping:
            if self.jump_recovery_elapsed >= self.config['jump_recovery_threshold']:
                self.is_jumping = True                  
                self.jump_duration_elapsed = 0
                self.jump_recovery_elapsed = 0
        
        if self.is_jumping:
            if keys[pygame.K_w] and not keys[pygame.K_s] and self.jump_duration_elapsed < self.config['jump_duration_threshold']:  # Durasi lompat jika di tahan -> sampai max                            
                self.rect.centery -= self.config['speedY'] * dt
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
            if self.airborne_elapsed > self.config['airborne_threshold']: #stop airborne if airborne_elapsed = max
                slowing = self.config['gravity']/2 if keys[pygame.K_w] else 0 
                self.rect.centery += (self.config['gravity'] - slowing) * dt
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

    def current_state(self, dt): #Update cooldown, grace, duration
        #Check phasing for hitbox radius
        if self.is_phasing: self.hitbox_radius = 0
        else: self.hitbox_radius = self.cur_hitbox
        
        #Hit Grace      
        if self.grace_active and pygame.time.get_ticks() - self.grace_timestamp >= self.config['grace_duration'] * 1000:
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
        n = 7  # more = smoother coverage

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
                                        self.rect.height / 2 * self.config['action_cd_max'])
        self.action_bar_rectMax.centerx = (self.rect.right + 20) if not self.facing_right else (self.rect.left - 20) #kebalikan facing
        self.action_bar_rectMax.centery = self.rect.centery
        
        self.action_bar_rect = pygame.Rect(0, 0, self.action_bar_rectMax.width, 
                                        self.rect.height / 2 * (self.config['action_cd_max'] - self.action_cd_remaining))
        self.action_bar_rect.x = self.action_bar_rectMax.x
        self.action_bar_rect.bottom = self.action_bar_rectMax.bottom

        # Phasing bar update
        self.phase_bar_rectMax = pygame.Rect(0, 0, self.rect.width * self.config['phase_max'], 10)
        self.phase_bar_rectMax.centerx = self.rect.centerx
        self.phase_bar_rectMax.centery = self.rect.bottom + 10
        self.phase_bar_rect = pygame.Rect(self.phase_bar_rectMax.left, self.phase_bar_rectMax.top,
                                        self.rect.width * self.phase_bar, 
                                        self.phase_bar_rectMax.height)
