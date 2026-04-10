import pygame
from Shared.constants import*
from Shared.utils import get_image

UI_FONT = None
font_size = 40

WIN_FONT = None
LOST_FONT = None
LOADING_FONT = None

def init_font():
    global UI_FONT, WIN_FONT, LOST_FONT, LOADING_FONT
    UI_FONT = pygame.font.Font("assets/Cirno.ttf", 40)
    UI_FONT.set_bold(True)
    WIN_FONT = pygame.font.Font("assets/Cirno.ttf", 72)
    WIN_FONT.set_bold(True)
    LOST_FONT = pygame.font.Font("assets/Cirno.ttf", 72)
    LOST_FONT.set_bold(True)
    LOADING_FONT = pygame.font.Font("assets/Cirno.ttf", 72)
    LOADING_FONT.set_bold(True)

def get_font(size, bold=True):
    font = pygame.font.Font("assets/Cirno.ttf", size)
    font.set_bold(bold)
    return font

def draw_ui(screen, player, boss_list):
    # Player UI
    p_text = UI_FONT.render(player.name.upper(), True, (192, 253, 253))
    screen.blit(p_text, (20, SCREEN_HEIGHT - font_size - 10))
    # HP Bar
    hp_gap = 1/player.max_hp * 420
    player_hp_bar_rect = pygame.Rect(-25, SCREEN_HEIGHT - font_size - 72, 600, 45)
    image = get_image("ui/hp_bar_player.png", player_hp_bar_rect, size_offsety=30)
    pygame.draw.rect(screen, BLACK, (102, SCREEN_HEIGHT - font_size - 40, 420, 25))
    if player.grace_active: 
        # pygame.draw.rect(screen, RED, (102 + hp_gap/2, SCREEN_HEIGHT - font_size - 40, player.hp/player.max_hp * 400, 25)) #grace hp = almost last hit
        pygame.draw.rect(screen, RED, (102 + hp_gap, SCREEN_HEIGHT - font_size - 40, player.hp/player.max_hp * 420, 25)) #grace hp

    pygame.draw.rect(screen, GREEN, (102, SCREEN_HEIGHT - font_size - 40, player.hp/player.max_hp * 420, 25))

    screen.blit(image, player_hp_bar_rect)
    
    # Absorb/Heal tracking
    absorb_txt = UI_FONT.render(f"Baka Stack: {player.absorb_count}/5", True, CYAN, (250,250,250))
    screen.blit(absorb_txt, (400, SCREEN_HEIGHT - font_size - 10))
    
    # Boss UI
    boss_counter = 0
    offset = -80
    for b in reversed(boss_list): #read in reverse, so boss1 on top of boss2
        if b:
            b_text = UI_FONT.render(f"{b.name} (Phase {min(b.current_phase, b.total_phases)}/{b.total_phases})", True, 
                                    WHITE if b.alive else RED2_0)
            b_rect = b_text.get_rect(topright=(SCREEN_WIDTH - 20, SCREEN_HEIGHT - font_size - 65 + offset * boss_counter))
            
            screen.blit(b_text, b_rect)
            
            bar_widthMax = 300
            bar_width = b.hp / b.max_hp * bar_widthMax
            bar_x = SCREEN_WIDTH - 20 - bar_widthMax
            pygame.draw.rect(screen, BLACK, (bar_x, SCREEN_HEIGHT - font_size - 20 + offset * boss_counter, bar_widthMax, 20))
            pygame.draw.rect(screen, RED2_0, (bar_x, SCREEN_HEIGHT - font_size - 20 + offset * boss_counter, bar_width, 20))
            pygame.draw.rect(screen, WHITE, (bar_x, SCREEN_HEIGHT - font_size - 20 + offset * boss_counter, bar_widthMax, 20), 2)
            pygame.draw.rect(screen, b.circle_color, (bar_x - 30, SCREEN_HEIGHT - font_size - 20 + offset * boss_counter, 20, 20)) # color indicator
            boss_counter += 1

def draw_win(screen):
    font = WIN_FONT
    text = font.render("You win. Press R to retry", True, WHITE)
    screen.fill(BLACK)
    screen.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))

def draw_lost(screen):
    font = LOST_FONT
    text = font.render("You LOST. Press R to retry", True, WHITE)
    screen.fill(BLACK)
    screen.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))

def draw_loading_screen(screen):
    font = LOADING_FONT
    text = font.render("Loading...", True, WHITE)
    screen.fill(BLACK)
    screen.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))