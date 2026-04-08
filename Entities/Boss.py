import pygame, math, random
from Shared.constants import*
from Entities.GameObject import GameObject
from Entities.Bullet import Bullet
from Entities.Particle import spawn_particles

class Boss(GameObject):
    def __init__(self, name, boss_data, start_x = SCREEN_WIDTH//2, direction = 1): # 1 to go right, -1 to go left 
        self.boss_data = boss_data
        self.phases = boss_data['phase']                                                                                  
        self.total_phases = len(self.phases)
        self.current_phase = 1
        size = boss_data['size']
        image = boss_data['boss_img']
        self.circle_color = boss_data['color']
        # data phase 1
        start_y = GROUND_Y - self.phases[str(self.current_phase)]['y_axis']
        super().__init__(x=start_x, y=start_y, width=size, height=size, hitbox_radius=30, image_path="boss/" + image, 
                                                                                    size_offsetx=125, size_offsety=125)
        self.name = name
        self.max_hp = self.phases[str(self.current_phase)]['max_hp']
        self.hp = self.max_hp
        self.grace_active = False
        self.grace_timestamp = 0
        self.grace_duration = 200
        self.alive = True

        self.base_y = float(start_y)
        self.bop_amplitude = 25
        self.bop_frequency = 3

        self.direction = direction # 1 for right, -1 for left
        self.fire_timer = 0
        self.spiral_angle = 0
        
    def update(self, dt, player, bullet_list):
        if not self.alive: return

        if self.grace_active and pygame.time.get_ticks() - self.grace_timestamp >= self.grace_duration:
            self.grace_active = False

        phase = self.phases[str(self.current_phase)]

        self._move(dt, phase)
            
        # Shooting logic
        self.fire_timer -= dt
        if self.fire_timer <= 0:
            self.fire_timer = phase['rate']
            if pygame.time.get_ticks() - player.grace_timestamp >= 1000: #delay after player get hit and first spawn
                self._shoot(player, bullet_list, phase)
            
    def draw(self, surface):
        if not self.alive: return
        color = self.boss_data['color']
        if not (self.grace_active and pygame.time.get_ticks() % 200 < 100): #efek kedip saat kena hit
            self.draw_hitcircle(surface, color, 6) #draw hitbox here is more like indicator in the middle, color for phase color
            self.draw_self(surface)
    
    def _move(self, dt, phase):
        #Transition phase movement
        new_axis = GROUND_Y - phase['y_axis']
        if abs(self.base_y - new_axis) > 2:
            if self.base_y < new_axis:
                self.base_y += 100 * dt
            else:
                self.base_y -= 100 * dt

        # Bop movement
        time = pygame.time.get_ticks() / 1000
        bop_offset = math.sin(time * self.bop_frequency) * self.bop_amplitude

        self.posY = self.base_y + bop_offset
        self.posX += phase['move_speed'] * self.direction * dt
        self.sync_rect()

        if self.rect.right > BG_WIDTH - BG_BORDER_X:
            self.direction = -1
        elif self.rect.left < BG_BORDER_X:
            self.direction = 1

    def _shoot(self, player, bullet_list, phase_data):
        pattern = phase_data['pattern']
        num_bullets = phase_data['num_bullet']
        spd = phase_data['bullet_spd']
        size = phase_data['bullet_size']
        image = phase_data['bullet_img'] + '.png'
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
                bullet_list.append(Bullet(cx, cy, bx, by, size, image, angle=angle))
                
        elif pattern == 'circle':
            step = (math.pi * 2) / num_bullets
            for i in range(num_bullets):
                a = step * i
                bx = math.cos(a) * spd
                by = math.sin(a) * spd
                angle = -math.degrees(math.atan2(by, bx))
                angle = round(angle / 5) * 5
                bullet_list.append(Bullet(cx, cy, bx, by, size, image, angle=angle))
                
        elif pattern == 'chaos': # Random from inside boss
            for i in range(num_bullets):
                a = random.uniform(0, math.pi * 2)
                bx = math.cos(a) * spd
                by = math.sin(a) * spd
                angle = -math.degrees(math.atan2(by, bx))
                angle = round(angle / 5) * 5
                bullet_list.append(Bullet(cx, cy, bx, by, size, image, angle=angle))

        elif pattern == 'random': # Random entire screen
            for i in range(num_bullets):
                side = random.choice(['top', 'right', 'left'])
                if side == 'top': # Fall down
                    cx = random.randint(0, BG_WIDTH) 
                    cy = -20
                    bx = random.uniform(-100, 100)
                    by = random.uniform(150, 300) 
                elif side == 'right': # Move left
                    cx = BG_WIDTH + 20
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
                bullet_list.append(Bullet(cx, cy, bx, by, size, image, angle=angle))
        
        elif pattern == 'spiral':
            # Circle ring that rotates each shot — looks like spinning arms at fast fire rates
            # num_bullet controls arms, rate controls spin speed
            step = (math.pi * 2) / num_bullets
            for i in range(num_bullets):
                a = step * i + self.spiral_angle
                bx = math.cos(a) * spd
                by = math.sin(a) * spd
                angle = -math.degrees(math.atan2(by, bx))
                angle = round(angle / 5) * 5
                bullet_list.append(Bullet(cx, cy, bx, by, size, image, angle=angle))
            self.spiral_angle += math.radians(20)  # rotate 20 degrees each shot
 
        elif pattern == 'burst':
            # Shotgun — tight cluster aimed at player with slight random noise per bullet
            # Feels different from fan: tighter, noisier, more panic-inducing
            angle_to_player = math.atan2(player.rect.centery - cy, player.rect.centerx - cx)
            for i in range(num_bullets):
                noise = random.uniform(-0.12, 0.12)  # ~7 degree noise
                a = angle_to_player + noise
                bx = math.cos(a) * spd
                by = math.sin(a) * spd
                angle = -math.degrees(math.atan2(by, bx))
                angle = round(angle / 5) * 5
                bullet_list.append(Bullet(cx, cy, bx, by, size, image, angle=angle))
 
        elif pattern == 'cross':
            # Rotated circle — always has one arm pointing at the player
            # num_bullet = number of arms (use 4 or 8)
            angle_to_player = math.atan2(player.rect.centery - cy, player.rect.centerx - cx)
            step = (math.pi * 2) / num_bullets
            for i in range(num_bullets):
                a = angle_to_player + step * i
                bx = math.cos(a) * spd
                by = math.sin(a) * spd
                angle = -math.degrees(math.atan2(by, bx))
                angle = round(angle / 5) * 5
                bullet_list.append(Bullet(cx, cy, bx, by, size, image, angle=angle))
 
        elif pattern == 'aimed':
            # Precise high-speed shots directly at the player
            # num_bullet = 1 is a single sniper shot, 2-3 adds a narrow flanking pair
            # Very different from fan — no forgiveness if player doesn't move
            angle_to_player = math.atan2(player.rect.centery - cy, player.rect.centerx - cx)
            for i in range(num_bullets):
                offset = (i - num_bullets // 2) * math.radians(8)  # 8 degrees between each
                a = angle_to_player + offset
                bx = math.cos(a) * spd
                by = math.sin(a) * spd
                angle = -math.degrees(math.atan2(by, bx))
                angle = round(angle / 5) * 5
                bullet_list.append(Bullet(cx, cy, bx, by, size, image, angle=angle))
                
    def take_damage(self, atk_dmg, particles_list):
        self.hp -= atk_dmg
        self.grace_timestamp = pygame.time.get_ticks()
        self.grace_active = True
        spawn_particles(self.rect.centerx, self.rect.centery, RED2_0, particles_list, 10) # Hit feedback
        if self.hp <= 0:
            self.current_phase += 1
            self._change_phase(particles_list)
            
    def _change_phase(self, particles_list):
        spawn_particles(self.rect.centerx, self.rect.centery, RED,  particles_list, count=30, is_burst=True) # Trigger massive death particle burst each transition 
        if self.current_phase > self.total_phases:
            self.alive = False
            spawn_particles(self.rect.centerx, self.rect.centery, RED2_0, particles_list, count=50, is_burst=True)
        else:
            self.max_hp = self.phases[str(self.current_phase)]['max_hp']
            self.hp = self.max_hp
