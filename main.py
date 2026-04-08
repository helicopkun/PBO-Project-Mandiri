import pygame, sys, random

from Shared.constants import*
from Shared.utils import load_json

from Entities.Player import Player

from Systems.Camera import Camera
from Systems.StageManager import StageManager
from Systems.ui import init_font, draw_ui, draw_win, draw_lost

pygame.init()
init_font()

screen_size = (SCREEN_WIDTH, SCREEN_HEIGHT) #just keep it 720p bro
screen = pygame.display.set_mode(screen_size) # Untuk UI dan lebar screen
pygame.display.set_caption("Maidenless Danmaku") # LMAOO AI got a hilarious name for ts
# Maidenless ~ a reference to Elden ring where the npc calls us maidenless
# Danmaku ~ bullet hell in japanese

# ================================================ Game loop setup ==========================================================================================================================================

# Player Load 
attack_type = load_json("player/attack.json")
PlayerTest = Player(name="HelicopKun", attack='slash')
#might do hotbar inventory-based attacks 1.slash, 2.Pierce, 3...

# Stage Load 
STAGES_ICY = load_json("stages/icy_cave.json")
stage = StageManager(STAGES_ICY)
stage.load_stage()

#background canvas
camera = Camera(PlayerTest)
world_surface = pygame.Surface((BG_WIDTH, BG_HEIGHT))


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

    #Update input
    cx, cy = camera.get_offset()
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
    click_state['pos'] = (mouse_pos[0] - cx,
                          mouse_pos[1] - cy)

    #Update current stage
    if stage.win: 
        draw_win(screen)
        if keys[pygame.K_r]: stage.retry(PlayerTest)
        continue
    if stage.lost: 
        draw_lost(screen)
        if keys[pygame.K_r]: stage.retry(PlayerTest)
        continue

    if all(not b.alive for b in stage.boss_list):
        if PlayerTest.rect.right >= SCREEN_WIDTH:
            stage.change_stage(screen, PlayerTest)
  
    # Update Entities
    stage.update_entities(dt, PlayerTest)

    if PlayerTest.is_hit: camera.trigger_shake()
    camera.update(dt)
    cx, cy = camera.get_offset()

    PlayerTest.update(keys, click_state, dt, stage.plat_list)
    

    
    # Draw objects
    stage.draw_stage(world_surface)

    PlayerTest.draw(world_surface)

    stage.draw_entities(world_surface)
    
    screen.blit(world_surface, (cx, cy))
    
    draw_ui(screen, PlayerTest, stage.boss_list)

    pygame.display.update()

pygame.quit()
sys.exit()