import pygame
from Shared.constants import *
from Shared.utils import get_image

UI_FONT = None
font_size = 40

def init_font():
    global UI_FONT
    UI_FONT = pygame.font.Font("assets/Cirno.ttf", font_size)
    UI_FONT.set_bold(True)

def get_font(size, bold=True):
    font = pygame.font.Font("assets/Cirno.ttf", size)
    font.set_bold(bold)
    return font

def draw_ui(surface, player, boss_list):
    # Player UI
    p_text = UI_FONT.render(player.name.upper(), True, (192, 253, 253))
    surface.blit(p_text, (20, SCREEN_HEIGHT - font_size - 10))
    # HP Bar
    hp_gap = 1/player.max_hp * 420
    player_hp_bar_rect = pygame.Rect(-25, SCREEN_HEIGHT - font_size - 72, 600, 45)
    image = get_image("ui/hp_bar_player.png", player_hp_bar_rect, size_offsety=30)
    pygame.draw.rect(surface, BLACK, (102, SCREEN_HEIGHT - font_size - 40, 420, 25))
    if player.grace_active: 
        # pygame.draw.rect(surface, RED, (102 + hp_gap/2, SCREEN_HEIGHT - font_size - 40, player.hp/player.max_hp * 400, 25)) #grace hp = almost last hit
        pygame.draw.rect(surface, RED, (102 + hp_gap, SCREEN_HEIGHT - font_size - 40, player.hp/player.max_hp * 420, 25)) #grace hp

    pygame.draw.rect(surface, GREEN, (102, SCREEN_HEIGHT - font_size - 40, player.hp/player.max_hp * 420, 25))

    surface.blit(image, player_hp_bar_rect)
    
    # Absorb/Heal tracking
    absorb_txt = UI_FONT.render(f"Baka Stack: {player.absorb_count}/5", True, CYAN, (250,250,250))
    surface.blit(absorb_txt, (400, SCREEN_HEIGHT - font_size - 10))
    
    # Boss UI
    boss_counter = 0
    offset = -80
    for b in reversed(boss_list): #read in reverse, so boss1 on top of boss2
        if b:
            b_text = UI_FONT.render(f"{b.name} (Phase {min(b.current_phase, b.total_phases)}/{b.total_phases})", True, 
                                    WHITE if b.alive else RED2_0)
            b_rect = b_text.get_rect(topright=(SCREEN_WIDTH - 20, SCREEN_HEIGHT - font_size - 65 + offset * boss_counter))
            
            surface.blit(b_text, b_rect)
            
            bar_widthMax = 300
            bar_width = b.hp / b.max_hp * bar_widthMax
            bar_x = SCREEN_WIDTH - 20 - bar_widthMax
            pygame.draw.rect(surface, BLACK, (bar_x, SCREEN_HEIGHT - font_size - 20 + offset * boss_counter, bar_widthMax, 20))
            pygame.draw.rect(surface, RED2_0, (bar_x, SCREEN_HEIGHT - font_size - 20 + offset * boss_counter, bar_width, 20))
            pygame.draw.rect(surface, WHITE, (bar_x, SCREEN_HEIGHT - font_size - 20 + offset * boss_counter, bar_widthMax, 20), 2)
            pygame.draw.rect(surface, b.circle_color, (bar_x - 30, SCREEN_HEIGHT - font_size - 20 + offset * boss_counter, 20, 20)) # color indicator
            boss_counter += 1

def draw_win(surface):
    font = get_font(72)
    text = font.render("You win", True, WHITE)
    text_rect = text.get_rect(center=(surface.get_width() // 2, surface.get_height() // 2))
    
    surface.fill(BLACK)
    surface.blit(text, text_rect)

def draw_lost(surface):
    font = get_font(72)
    text = font.render("You LOST", True, WHITE)
    text_rect = text.get_rect(center=(surface.get_width() // 2, surface.get_height() // 2))
    
    surface.fill(BLACK)
    surface.blit(text, text_rect)