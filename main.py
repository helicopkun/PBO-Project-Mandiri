import pygame, sys, random

from Entities.Player import Player
from Entities.Particle import particles

from Shared.constants import*
from Shared.utils import load_json, circle_collide

from Systems.StageManager import StageManager
from Systems.ui import init_font, draw_ui

pygame.init()
init_font()


screen = pygame.display.set_mode((WIDTH, HEIGHT)) # Untuk UI
pygame.display.set_caption("Maidenless Danmaku") # LMAOO AI got a hilarious name for ts
# Maidenless ~ a reference to Elden ring where the npc calls us maidenless
# Danmaku ~ bullet hell in japanese

# ================================================ Game loop setup ==========================================================================================================================================

# Stage Load 
STAGES_ICY = load_json("stages/icy_cave.json")
stage = StageManager(STAGES_ICY)
stage.load_stage()


# Player Load 
attack_type = load_json("player/attack.json")
PlayerTest = Player(name="HelicopKun", attack='slash')
#might do hotbar inventory-based attacks 1.slash, 2.Pierce, 3...


# Screen Shake Variables
shake_timer = 0
world_surface = pygame.Surface((WIDTH, HEIGHT))

#Debugging
show_hitbox = False
show_player_hitbox = False
show_bullet_hitbox = True
show_atk_hitbox = True
show_img_rect = False

clock = pygame.time.Clock()
time_scale = 1.0

running = True
# ================================================ Game loop ==========================================================================================================================================

while running:
    # print(clock.get_fps())
    # dt = clock.tick(60) / 1000  # .tick(framerate) mengembalikan waktu ms antar frame, ms / 1000 = detik

    og_dt = clock.tick(60) / 1000  #slow-mo effect when overloaded, use when having too much frame drops
    og_dt = min(og_dt, 0.033)  # cap at ~30 FPS equivalent
    
    fps = clock.get_fps() 
    if fps < 55: time_scale += (fps / 60 - time_scale) * 5 * og_dt
    else: time_scale += (1.0 - time_scale) * 5 * og_dt
    time_scale = max(0.5, min(time_scale, 1.2))

    target_dt = 1 / 60
    dt = target_dt * time_scale
    
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
    
    if all(not b.alive for b in stage.boss_list):
        if not stage.stage_counter > stage.total_stage:
            stage.change_stage()
            continue

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
                if stage.bullet_list: stage.bullet_list.remove(bullet)
                stage.bullet_list.clear() #remove all bullet
                shake_timer = 0.25 # Trigger Screen Shake
                if PlayerTest.hp <= 0:
                    print("GAME OVER") # will make a retry/quit button
                    #running = False
                continue
    
    if shake_timer > 0:
        shake_timer -= dt

    
    # Draw objects 
    world_surface.blit(stage.bg, (0,0))
    
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