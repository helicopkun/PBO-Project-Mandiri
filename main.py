import pygame, sys

from Shared.constants import SCREEN_HEIGHT, SCREEN_WIDTH, BG_WIDTH, BG_HEIGHT, BG_BORDER_X
from Shared.utils import load_json, preload_assets

from Entities.Player import Player

from Systems.Camera import Camera
from Systems.StageManager import StageManager
from Systems.ui import init_font, draw_ui, draw_win, draw_lost, draw_loading_screen, draw_stage_clear, draw_next_stage_arrow, draw_pause

pygame.init()
init_font()

screen_size = (SCREEN_WIDTH, SCREEN_HEIGHT) #just keep it 720p bro
screen = pygame.display.set_mode(screen_size) # Untuk UI dan lebar screen
pygame.display.set_caption("Maidenless Danmaku") # LMAOO AI got a hilarious name for ts
# Maidenless ~ a reference to Elden ring where the npc calls us maidenless
# Danmaku ~ bullet hell in japanese

# ================================================ Game loop setup ==========================================================================================================================================
atk_data = load_json("player/attack.json")
draw_loading_screen(screen)
pygame.display.update()
preload_assets(atk_data)

player = Player(name="HelicopKun")
#might do hotbar inventory-based attacks 1.slash, 2.Pierce, 3...

STAGES_ICY = load_json("stages/icy_cave.json")
STAGES_RANDOM_ICY = load_json("stages/icy_random.json")

stage = StageManager(STAGES_RANDOM_ICY)
stage.load_stage(screen, player)

#Test BGM - Music by Misty Studio - https://www.youtube.com/watch?v=2UvlqIUa0B0
# pygame.mixer.music.load("assets/bgm/Strongest Maidenless Fairy.ogg")
# pygame.mixer.music.set_volume(0.3)
# pygame.mixer.music.play(-1)

camera = Camera(player) #screen canvas position
world_surface = pygame.Surface((BG_WIDTH, BG_HEIGHT)) #background canvas

drawn = False
clock = pygame.time.Clock()

running = True
paused = False
# ================================================ Game loop ==========================================================================================================================================

while running:
    # print(clock.get_fps())
    dt = clock.tick(60) / 1000  # .tick(framerate) mengembalikan waktu ms antar frame, ms / 1000 = detik
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                paused = not paused
                # pygame.mixer.music.unpause()

    cx, cy = camera.get_offset()
    if paused:
        # pygame.mixer.music.pause()
        screen.blit(world_surface, (cx, cy))
        draw_ui(screen, player, stage)
        draw_pause(screen)
        pygame.display.update()
        continue 

    #Update input
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
    if stage.lost or stage.win:
        if keys[pygame.K_r]:
            stage.retry(screen, player)
            cx, cy = camera.get_snap() # snap to default pos (border, ground)
            clock.tick() #reset clock, so it doesnt make entity teleport
            drawn = False
        elif not drawn:
            if stage.lost:
                pygame.time.delay(1000)
                player.draw_self(world_surface)
                draw_lost(screen)
            elif stage.win: 
                draw_win(screen)
            pygame.display.update()
            drawn = True
        continue
    
    if stage.cleared:
        if player.rect.right >= BG_WIDTH - BG_BORDER_X:
            stage.change_stage(screen, player)
            cx, cy = camera.get_snap()
            clock.tick()
            continue

    # Update Entities
    stage.update_entities(dt, player)

    if player.is_hit: camera.trigger_shake()
    camera.update(dt)
    cx, cy = camera.get_offset()

    player.update(keys, click_state, dt, stage.plat_list)
    

    # Draw objects
    stage.draw_stage(world_surface) # add objects inside world
    player.draw_self(world_surface)
    stage.draw_entities(world_surface)
    
    screen.blit(world_surface, (cx, cy)) # display object in camera
    
    if stage.cleared:
        draw_stage_clear(screen, pygame.time.get_ticks() - stage.clear_timestamp)
        draw_next_stage_arrow(screen, pygame.time.get_ticks())
        
    draw_ui(screen, player, stage)

    pygame.display.update()

pygame.quit()
sys.exit()