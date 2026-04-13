import pygame, math
from Shared.constants import*
from Shared.utils import load_json, get_sound, get_image, update_animation
from Entities.GameObject import GameObject
from Entities.Particle import spawn_particles

class Player(GameObject):
    def __init__(self, name = "Baka", state = "idle", attack = 'slash'):
        self.config = load_json("player/config.json")
        self.attack_data = load_json("player/attack.json")

        super().__init__(x= BG_BORDER_X + 10, y=GROUND_Y, width=80, height=100, hitbox_radius=self.config['hitbox'],
                         image_path=f"cirno/{state}.png", size_offsetx=50, size_offsety=30)

        # elapsed -> stopwatch (0,1,2, until n) counting up <-> threshold
        # timestamp -> records the time an action triggered <-> duration
        # remaining -> timer (n, n-1, 0) counting down
        
        self.name = name
        self.cur_hitbox = self.hitbox_radius

        self.max_hp = self.config['max_hp']
        self.hp = self.max_hp
        self.is_dead = False
        self.is_hit = False
        self.grace_active = False # i-frame setelah kena hit
        self.grace_timestamp = 0

        self.vx = 0.0
        self.vy = 0.0

        self.is_phasing = False
        self.phase_bar = self.config['phase_max']
        self.phase_recharge_timestamp = 0

        self.is_jumping = False
        self.jump_duration_elapsed = 0
        self.jump_recovery_elapsed = 0
        self.airborne_elapsed = 0

        self.current_platform = None
        self.platform_group = None
        self.quickfall_plat_elapsed = 0
        self.old_bottom = self.rect.bottom
        
        self.stamina_bar = self.config['stamina_max']
        self.stamina_recharge_timestamp = 0
        self.is_exhausted = False #action allowance
        self.scale_rate = 1.0 #action efficiency 
        
        self.action_cd_remaining = 0
        
        self.absorb_active = False
        self.absorb_count = 0 
        self.absorbed_this_window = 0
        
        self.attack_type = attack
        self.attack_type_data = self.attack_data[attack]
        self.active_attacks = []
        self.copy_rect = None #copying self old pos
        
        self.facing = 'right'
        self.facing_angle = 0
        self.facing_right = True
        self.look_attack_timestamp = 0
        self.look_jump_timestamp = 0

    def update(self, keys, click_state, dt, platforms):
        self.platform_group = platforms
        self._tick(dt)
        
        # Movement - freeze when absorbing
        if not self.absorb_active:
            self._move(keys, dt) 
        
        self._facing_indicator(keys, click_state)
        
        # Actions
        self._actions(keys, click_state)

        #Character Image
        self.image_path = f"cirno/{self._get_state(keys)}.png"
        self.image = get_image(image_path=self.image_path, flipx=0 if self.facing_right else 1, rect=self.rect, 
                                                                                            size_offsetx=50, 
                                                                                            size_offsety=30)
                
    def draw_self(self, surface):
        self.image.set_alpha(100 if self.is_phasing else 255)
        if not (self.grace_active and pygame.time.get_ticks() % 200 < 100): #efek kedip saat kena hit
            super().draw_self(surface)
            
        if show_player_hitbox: self.draw_hitcircle(surface, color=YELLOW, hitbox_radius=self.cur_hitbox, border_width=3)
        
        #Attack
        for atk in self.active_attacks:
            atk_type = atk['type_data']
            if atk['cur_frame'] >= atk_type['frame_count']:
                self.active_attacks.remove(atk)
            else: 
                current_img = atk['images'][atk['cur_frame']]
                atk['cur_frame'], atk['frame_timestamp'] = update_animation(surface, current_img, atk['center'], 
                                                                            atk_type['frame_count'], atk['cur_frame'], 
                                                                            atk_type['duration'], atk['frame_timestamp'])
            if show_atk_hitbox:
                for hitbox in atk['hitboxes']:
                    pygame.draw.rect(surface, YELLOW, hitbox, 2)
                for hitbox in atk['active_hitboxes']:
                    pygame.draw.rect(surface, RED2_0, hitbox, 2)


    def _tick(self, dt): #Update cooldown, grace, duration
        self.is_hit = False

        # Hit Grace      
        if pygame.time.get_ticks() - self.grace_timestamp >= self.config['grace_duration'] * 1000:
            self.grace_active = False

        # Phase
        if pygame.time.get_ticks() - self.phase_recharge_timestamp >= self.config['phase_recharge_delay'] * 1000: # Recharge after CD
            self.phase_bar += self.config['phase_rate'] * dt * self.scale_rate
            self.phase_bar = min(self.config['phase_max'], self.phase_bar)

        # Stamina
        if self.stamina_bar < 0:
            if not self.is_exhausted: # cheap 1 time play sfx
                sound = get_sound("player_exhausted.wav")
                sound.set_volume(0.5)
                sound.play()
            self.absorb_active = False
            self.active_attacks.clear()
            self.is_exhausted = True
            self.scale_rate = 0.7
        
        if self.stamina_bar > self.config['stamina_max'] / 4:
            self.is_exhausted = False
            self.scale_rate = 1.0

        if pygame.time.get_ticks() - self.stamina_recharge_timestamp >= self.config['stamina_recharge_delay'] * 1000:
            self.stamina_bar += self.config['stamina_rate'] * dt *  self.scale_rate
            self.stamina_bar = min(self.config['stamina_max'], self.stamina_bar)

        # Action - internal cd
        if self.action_cd_remaining > 0:
            self.action_cd_remaining -= dt

        # Absorb
        if self.absorb_active:
            self.cur_hitbox = self.config['absorb_radius']
            self.absorb_timer -= dt
            if self.absorb_timer <= 0:
                self.absorb_active = False
                self.absorbed_this_window = 0

        # Attack
        for atk in reversed(self.active_attacks): # read in reverse for safely removing atk
            self._attacking(atk)
            if atk['target']:
                for enemy in list(atk['target']): #reduce tick_rate cd 
                    if atk['target'][enemy] > 0:
                        atk['target'][enemy] -= dt 
          
    def _get_state(self, keys):
        if self.is_dead: return 'dead'
        if self.grace_active: return 'hit'
        if self.is_exhausted: return 'exhausted'
        if self.is_phasing: return 'phase'
        if pygame.time.get_ticks() - self.look_attack_timestamp < 400: return 'attack'
        if self.absorb_active: return 'absorb'
        if self.is_jumping: return 'jump'
        if self.airborne_elapsed > 0:
            if keys[pygame.K_s]: return 'quickfall'
            if keys[pygame.K_w]: return 'slowfall'
        if self.airborne_elapsed > 0: return 'falling'
        if abs(self.vx) > 5:
            cycle = pygame.time.get_ticks() % 750
            if cycle < 250 : return 'walk-0'
            if 250 < cycle < 500: return 'walk-1'
            if cycle > 500: return 'walk-2'
        
        return 'idle'
        

    def take_damage(self, particles_list):
        self.hp -= 1
        sound = get_sound("player_hit.wav")
        sound.set_volume(0.5)
        sound.play()
        if self.hp <= 0:
            self.is_dead = True
            return
        self.grace_timestamp = pygame.time.get_ticks()
        self.grace_active = True
        spawn_particles(self.rect.centerx, self.rect.centery, RED2_0, particles_list, 10)
        self.is_hit = True

    def _actions(self, keys, click_state):
        #Hotbar
        attack_list = ['slash', 'pierce']
        picked_attack = self.attack_type
        if keys[pygame.K_1]: picked_attack = attack_list[0]
        elif keys[pygame.K_2]: picked_attack = attack_list[1]
        if picked_attack != self.attack_type:
            sound = get_sound("player_select.wav")
            sound.set_volume(0.5)
            sound.play()
            self.attack_type = picked_attack
            self.attack_type_data = self.attack_data[self.attack_type]
        
        if self.action_cd_remaining > 0 or self.is_exhausted or self.grace_active or self.is_phasing or self.absorb_active:
            return
        
        stamina_grace = self.stamina_bar > 0 #check before decreasing
        #Absorb
        if (keys[pygame.K_l] or click_state['right']):                                            
            self.absorb_active = True
            self.absorb_timer = self.config['absorb_duration']

            self.stamina_bar -= self.config['absorb_stamina']
            self.action_cd_remaining = self.config['absorb_cd']

        #Attack
        if (keys[pygame.K_k] or click_state['left']):
            sound = get_sound(self.attack_type_data['sfx'])
            sound.set_volume(1.0)
            sound.play()
            self.look_attack_timestamp = pygame.time.get_ticks()

            self.stamina_bar -= self.attack_type_data['stamina_reduce']
            self.action_cd_remaining = self.attack_type_data['action_cd']

            attack_images = [] #get image and reset if it existed
            offset_dist = 300 * self.attack_type_data['scale']
            angle = math.radians(self.facing_angle)
            for i in range(self.attack_type_data['frame_count']):
                attack_images.append(get_image(f"attack/{self.attack_type}/{self.attack_type}-{i}.png", 
                                                    angle=self.facing_angle, scale=self.attack_type_data['scale']))
            atk_image_center = ( # get setup pos (static pos)
                self.rect.centerx + math.cos(angle) * offset_dist,
                self.rect.centery + math.sin(-angle) * offset_dist
            )
            self.copy_rect = self.rect.copy()
            base_hitboxes = self._generate_attack_hitbox() # pathway for active hitbox
            new_attack = { # get data for attack
                'type': self.attack_type,
                'type_data': self.attack_type_data,
                'images': attack_images,
                'center': atk_image_center,
                'hitboxes': base_hitboxes,
                'active_hitboxes': [],
                'target': {}, # add enemy: tick, enemy for checking tick-rate of said attack
                'cur_frame': 0,
                'frame_timestamp': 0
            }   
            self.active_attacks.append(new_attack)
        
        if (keys[pygame.K_l] or click_state['right']) or (
            keys[pygame.K_k] or click_state['left']):
            self.stamina_recharge_timestamp = pygame.time.get_ticks()
            if stamina_grace: self.stamina_bar = max(0, self.stamina_bar)

    def absorbed(self, bullet, particles_list): #succesful absorb
        if self.absorbed_this_window >= self.config['absorbed_this_window_max']: return
        print("here")
        self.absorbed_this_window += 1
        self.absorb_count += 1
        self.phase_bar = min(self.config['phase_max'], self.phase_bar + self.config['phase_max']/4)
        self.stamina_bar = min(self.config['stamina_max'], self.stamina_bar + self.config['absorb_stamina']/5)
        self.absorb_timer = min(self.config['absorb_duration'] , self.absorb_timer + self.config['absorb_duration']/3)
        # self.action_cd_remaining = max(0, self.action_cd_remaining - self.config['absorb_cd']/2)
        spawn_particles(bullet.rect.centerx, bullet.rect.centery, CYAN2_0, particles_list, 6) # Absorb Sparks
        if self.absorb_count >= 5:
            self.hp = min(self.hp + 1, self.max_hp)
            self.absorb_count = 0
            spawn_particles(self.rect.centerx, self.rect.centery, GREEN, particles_list, 15) # Heal Sparks

    def attacked(self, enemy, atk, particle_list): #succesful attack, atk = general data of attack , atk_type = specific (slash, pierce, etc..)
        if enemy.hp <= 0 or enemy.grace_active:
            return
        
        atk_type = atk['type_data']
        
        if atk_type['damage_tick'] == 'single': # hit once after colision
            if enemy in atk['target']:
                return 
            atk['target'][enemy] = -1 #flag = already attacked, to add enemy in target
            # self.stamina_bar = max(0 , self.stamina_bar - atk_type['stamina_reduce']) # lower cd if succesful single-hit attack #skipped feature


        tick = 0.15
        if atk_type['damage_tick'] == 'multi': # hit every tick-rate per colision
            if enemy in atk['target'] and atk['target'][enemy] > 0:
                return
            atk['target'][enemy] = tick
        
        enemy.take_damage(atk_type['damage'], particle_list)


    def _attacking(self, atk): #generate active frame hitbox for specific attack
        atk['active_hitboxes'].clear()# Reset active hitboxes every frame
        start_frame = atk['type_data']['active_frames'][0]
        end_frame = min(atk['type_data']['active_frames'][1],
                        atk['type_data']['frame_count'] - 1) #desync measure

        if start_frame <= atk['cur_frame'] <= end_frame: #check if in the active frame window
            total_active_frames = max(1, end_frame - start_frame) # prevent division by zero
            progress = (atk['cur_frame'] - start_frame) / total_active_frames
            total_hitboxes = len(atk['hitboxes'])

            if atk['type'] == 'slash': # --- THE SWEEP LOGIC --- Visual: {}{}[>][>]{}{} -> Sweeps across the chain
                current_tip = int(progress * total_hitboxes)
                hitbox_length = 4 
                start_idx = max(0, current_tip - hitbox_length) # hitbox tail
                atk['active_hitboxes'] = atk['hitboxes'][start_idx : current_tip]

            elif atk['type'] == 'pierce': # --- THE GROW LOGIC --- Visual: [>][>][>]{}{} -> Grows from base to tip
                current_tip = int(progress * total_hitboxes)
                atk['active_hitboxes'] = atk['hitboxes'][:current_tip]
            
            else: # Default fallback (Spin / All at once)
                atk['active_hitboxes'] = atk['hitboxes'].copy()
            
    def _generate_attack_hitbox(self): # generate chain hitbox trajectory, not needing atk data because only load ONCE during the trigger phase
        n = 8  # more = smoother coverage

        if self.attack_type == 'slash':
            length = 6.5 * 100
            thickness = 1.5 * 100
        if self.attack_type == 'pierce': 
            length = 6.5 * 100 * 2.5
            thickness = 1.5 * 100

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


    def _on_platform(self):
        for platform in self.platform_group:
            if self.rect.right > platform.rect.left and self.rect.left < platform.rect.right: # ketika ujung player memasuki area platform
                if self.rect.bottom >= platform.rect.top and self.old_bottom <= platform.rect.top + 10:
                    self.current_platform = platform
                    return True
        self.current_platform = self.platform_group[0]
        return False
    
    def _move(self, keys, dt):
        on_plat = self._on_platform() #cache on_plat if dont need to check all the time
        self.old_bottom = self.rect.bottom # save old footing
            
        #Phasing movement
        if keys[pygame.K_LSHIFT] and not (self.grace_active or self.is_exhausted):
            self.phase_recharge_timestamp = pygame.time.get_ticks()
            self.stamina_recharge_timestamp = pygame.time.get_ticks()
        
        if keys[pygame.K_LSHIFT] and not (self.grace_active or self.is_exhausted) and self.phase_bar > 0:
                self.phase_bar -= dt
                self.cur_hitbox = 0
                self.is_phasing = True 
        else:
            self.cur_hitbox = self.hitbox_radius
            self.is_phasing = False

        if self.is_phasing:
            dx = 0
            dy = 0
            if keys[pygame.K_w]: dy = -1 
            if keys[pygame.K_s]: dy = 1 

            if dy == 0: 
                dx = 0.5 if self.facing_right else -0.5 #keep moving if keys arent pressed
            if keys[pygame.K_d] and not keys[pygame.K_a]: dx = 1
            if keys[pygame.K_a] and not keys[pygame.K_d]: dx = -1 

            if dx != 0 and dy != 0:
                length = math.hypot(dx, dy)
                dx /= length
                dy /= length
        
            self.rect.centerx += dx * self.config['speedX'] * dt * self.config['phase_spd'] * self.scale_rate
            self.rect.left = max(BG_BORDER_X, self.rect.left)
            self.rect.right = min(BG_WIDTH - BG_BORDER_X, self.rect.right)
            
            self.rect.centery += dy * self.config['speedY'] * dt * self.config['phase_spd'] * self.scale_rate
            self.rect.top = max(BG_BORDER_Y, self.rect.top)
            self.rect.bottom = min(GROUND_Y, self.rect.bottom)
            return


        #Horizontal movement
        target_vx = 0
        accel = self.config['accel'] 

        if keys[pygame.K_d] and not keys[pygame.K_a]: target_vx =  self.config['speedX']
        if keys[pygame.K_a] and not keys[pygame.K_d]: target_vx = -self.config['speedX']

        self.vx += (target_vx - self.vx) * accel * dt

        self.rect.centerx += self.vx * dt * self.scale_rate
        self.rect.left  = max(BG_BORDER_X, self.rect.left)
        self.rect.right = min(BG_WIDTH - BG_BORDER_X, self.rect.right)

        #Vertical movement
        if keys[pygame.K_s]:
            allow_quickfall = self.quickfall_plat_elapsed >= self.config['quickfall_plat_threshold']
            self.rect.centery += self.config['speedY'] * dt * self.scale_rate

            if self._on_platform() and not allow_quickfall: 
                self.rect.bottom = self.current_platform.rect.top
            else:
                self.rect.bottom = min(GROUND_Y, self.rect.bottom)

        if keys[pygame.K_s] and self._on_platform(): self.quickfall_plat_elapsed += dt
        else :                                       self.quickfall_plat_elapsed = 0

        if keys[pygame.K_w] and on_plat and not (self.is_jumping or keys[pygame.K_s]):
            if self.jump_recovery_elapsed >= self.config['jump_recovery_threshold']:
                sound = get_sound("player_jump.wav")
                sound.set_volume(0.9)
                sound.play()
                self.is_jumping = True                  
                self.jump_duration_elapsed = 0
                self.jump_recovery_elapsed = 0
        
        if self.is_jumping:
            if keys[pygame.K_w] and not keys[pygame.K_s] and self.jump_duration_elapsed < self.config['jump_duration_threshold']:  # Durasi lompat jika di tahan -> sampai max                            
                self.rect.centery -= self.config['speedY'] * dt * self.scale_rate
                self.rect.top = max(BG_BORDER_Y, self.rect.top)
                self.jump_duration_elapsed += dt
            else:
                self.is_jumping = False
        
        if not self.is_jumping:
            #Gravitasi
            if not self._on_platform():
                self.airborne_elapsed += dt # set airborne
                if self.airborne_elapsed > self.config['airborne_threshold']: #stop airborne if airborne_elapsed = max
                    slowing = self.config['gravity']/2 if keys[pygame.K_w] else 0 
                    self.rect.centery += (self.config['gravity'] - slowing) * dt
                    self.rect.bottom = min(GROUND_Y, self.rect.bottom)

            #Reset airborne, cooldown jump, etc jika berada di platform
            if self._on_platform():
                self.jump_recovery_elapsed += dt * self.scale_rate
                self.airborne_elapsed = 0

    def _facing_indicator(self, keys, click_state):
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
                
                if pygame.time.get_ticks() - self.look_jump_timestamp >= 250: # delay after jump
                    self.facing = 'right' if self.facing_right else 'left'
                
        # Attack facing indicator
        if self.action_cd_remaining <= 0:
            direction = ['right', 'top-right', 'up', 'top-left', 'left', 'bottom-left', 'down', 'bottom-right']
            if click_state['left']:
                mx , my = click_state['pos']
                dx = mx - self.rect.centerx
                dy = my - self.rect.centery

                self.facing_angle = math.degrees(math.atan2(-dy, dx))
                self.facing_angle = self.facing_angle % 360
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
    