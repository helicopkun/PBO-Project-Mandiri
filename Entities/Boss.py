import pygame, math, random
from Shared.constants import*
from Entities.GameObject import GameObject
from Entities.Bullet import Bullet
from Entities.Particle import spawn_particles

class Boss(GameObject):
    def __init__(self, name, boss_data, start_x = BG_WIDTH//2, direction = 1): # 1 to go right, -1 to go left 
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

        #Bop
        self.base_y = float(start_y)
        self.bop_amplitude = 25
        self.bop_frequency = 3
        self.direction = direction # 1 for right, -1 for left

        #Box
        margin = size
        left   = BG_BORDER_X + margin
        right  = BG_WIDTH - BG_BORDER_X - margin
        top    = BG_BORDER_Y + margin
        bottom = GROUND_Y - margin
        self.box_corners = [(left, top), (right, top), (right, bottom), (left, bottom)]
        self.box_target_idx = 0

        #Random
        self.move_angle = random.uniform(0, math.pi * 2)

        #Shoot
        self.fire_timer = 0
        self.spiral_angle = 0
        
    def update(self, dt, player, bullet_list):
        if not self.alive: return

        if self.grace_active and pygame.time.get_ticks() - self.grace_timestamp >= self.grace_duration:
            self.grace_active = False

        phase = self.phases[str(self.current_phase)]

        self._move(dt, phase, player)
            
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
    

    def _move(self, dt, phase, player):
        if 'movement' not in phase: self._move_bop(dt, phase)
        else:    
            if phase['movement'] == 'bop': self._move_bop(dt, phase)
            if phase['movement'] == 'box': self._move_box(dt, phase)
            if phase['movement'] == 'chase': self._move_chase(dt, phase, player)
            if phase['movement'] == 'random': self._move_random_angle(dt, phase)
            if phase['movement'] == 'middle': self._move_middle(dt, phase)

        self.sync_rect()

    def _move_bop(self, dt, phase):
        #Transition phase movement
        new_axis = GROUND_Y - phase['y_axis']
        if abs(self.base_y - new_axis) > 2:
            self.base_y += 100 * dt if self.base_y < new_axis else -100 * dt
        #Bop
        time = pygame.time.get_ticks() / 1000
        bop_offset = math.sin(time * self.bop_frequency) * self.bop_amplitude
        if self.rect.right > BG_WIDTH - BG_BORDER_X: self.direction = -1
        elif self.rect.left < BG_BORDER_X:           self.direction =  1
        self.posY = self.base_y + bop_offset
        self.posX += phase['move_speed'] * self.direction * dt

    def _move_box(self, dt, phase):
        target = self.box_corners[self.box_target_idx]
        tx, ty = target
        dx = tx - self.posX
        dy = ty - self.posY
        dist = math.hypot(dx, dy)

        if dist < 5:  # close enough, go to next corner
            self.box_target_idx = (self.box_target_idx + 1) % 4
        else:
            spd = phase['move_speed']
            self.posX += (dx / dist) * spd * dt
            self.posY += (dy / dist) * spd * dt
            
    def _move_chase(self, dt, phase, player):
        dx = player.rect.centerx - self.posX
        dy = player.rect.centery - self.posY
        dist = math.hypot(dx, dy)

        if dist > self.width*1.5:
            spd = phase['move_speed']
            spd = max(spd, player.config['speedX'] / 2)
            self.posX += (dx / dist) * spd * dt
            self.posY += (dy / dist) * spd * dt

        # clamp to arena
        self.posX = max(BG_BORDER_X + self.width//2,  min(BG_WIDTH - BG_BORDER_X - self.width//2,  self.posX))
        self.posY = max(BG_BORDER_Y + self.height//2, min(GROUND_Y - self.width//2,                self.posY))

    def _move_random_angle(self, dt, phase):
        spd = phase['move_speed']
        self.posX += math.cos(self.move_angle) * spd * dt
        self.posY += math.sin(-self.move_angle) * spd * dt #pygame Y coord flipped

        new_angle = None                                                #10* offset from wall
        if self.posX > BG_WIDTH - BG_BORDER_X - self.width//2:  new_angle = random.uniform(100, 260) # 90, 270, right
        elif self.posX < BG_BORDER_X + self.width//2:           new_angle = random.uniform(-80, 80) # -90, 90, left
        elif self.posY > GROUND_Y - self.width//2:              new_angle = random.uniform(10, 170) # 0, 180, bottom
        elif self.posY < BG_BORDER_Y + self.width//2:           new_angle = random.uniform(190, 350) # 180, 360, top
        
        if new_angle != None:
            self.move_angle = math.radians(new_angle) 
            self.posX = max(BG_BORDER_X + self.width//2,  min(BG_WIDTH - BG_BORDER_X - self.width//2,  self.posX))
            self.posY = max(BG_BORDER_Y + self.height//2, min(GROUND_Y - self.width//2, self.posY))

    def _move_middle(self, dt, phase):
        target = (BG_WIDTH//2 - self.width//2, BG_HEIGHT//2 - self.width//2) # middle arena
        dx = target[0] - self.posX
        dy = target[1] - self.posY
        dist = math.hypot(dx, dy)
        if dist < 5: return
        spd = phase['move_speed']
        self.posX += (dx / dist) * spd * dt
        self.posY += (dy / dist) * spd * dt


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
            self.base_y = self.posY
