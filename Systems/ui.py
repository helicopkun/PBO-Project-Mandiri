import pygame
from Shared.constants import*
from Shared.utils import get_image, draw_slanted_bar, draw_slanted_bar_alpha, draw_radial_bar

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

def _draw_stage_counter(screen, stage):
    font = get_font(28)
    text = font.render(f"STAGE {stage.stage_counter} / {stage.total_stage}", True, WHITE)
    rect = text.get_rect(midtop=(SCREEN_WIDTH // 2, 10))
    
    panel = pygame.Rect(rect.left - 10, rect.top - 2, rect.width + 20, rect.height + 4)
    draw_slanted_bar_alpha(screen, (0, 0, 0, 140), panel, 8)
    draw_slanted_bar_alpha(screen, WHITE, panel, 8, 2)
    
    screen.blit(text, rect)

def _draw_hotbar(screen, player):
    slot_size = 60
    padding = 8
    num_slots = len(player.attack_data)
    total_width = num_slots * (slot_size + padding) - padding

    start_x = SCREEN_WIDTH // 2 - total_width // 2
    y = SCREEN_HEIGHT - 80
    key_font = get_font(18)

    for i, atk in enumerate(player.attack_data):
        x = start_x + i * (slot_size + padding)
        slot_rect = pygame.Rect(x, y, slot_size, slot_size)
        is_active = (atk == player.attack_type)

        # Background
        bg_color = (0, 0, 0, 160) if not is_active else (40, 40, 80, 200)
        pygame.draw.rect(screen, bg_color, slot_rect)

        # Icon
        icon = get_image(f"attack/{atk}/{atk}.png", slot_rect)
        screen.blit(icon, (x, y))

        # Outline — glows yellow if active
        outline_color = YELLOW if is_active else WHITE
        outline_width = 3 if is_active else 2
        pygame.draw.rect(screen, outline_color, slot_rect, outline_width)

        # Keybind
        key_text = key_font.render(str(i + 1), True, YELLOW if is_active else WHITE)
        screen.blit(key_text, (slot_rect.right - key_text.get_width() - 4,
                               slot_rect.top + 2))

def draw_ui(screen, player, stage): #ts is my weakness
    _draw_stage_counter(screen, stage)
    
    #Player overlay
    overlay = pygame.Surface((600, 120), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 70))  # semi-transparent black
    screen.blit(overlay, (0, SCREEN_HEIGHT - 120))
    #Boss overlay
    boss_count = len(stage.boss_list)
    overlay_h = 120 + max(0, (boss_count - 1) * 80)
    right_overlay = pygame.Surface((600, overlay_h), pygame.SRCALPHA)
    right_overlay.fill((0, 0, 0, 70))
    screen.blit(right_overlay, (SCREEN_WIDTH - 600, SCREEN_HEIGHT - overlay_h))

    # Player UI
    # Name
    p_text = UI_FONT.render(f"{player.name.upper()}\t Baka Stack: {player.absorb_count}/5", True, (192, 253, 253))
    # HP
    player_hp_img_rect = pygame.Rect(-25, SCREEN_HEIGHT - font_size - 72, 600, 45)
    image = get_image("ui/hp_bar_player.png", player_hp_img_rect, size_offsety=30)
    hp_gap = 1/player.max_hp * 420
    hp_rect = pygame.Rect(100, SCREEN_HEIGHT - font_size - 40, 420, 25)
    
    # Stamina Bar update
    stamina_bar_length = 350
    stamina_bar_max = pygame.Rect(0, 0, stamina_bar_length, 15)
    stamina_bar_max.left =  hp_rect.left + 10
    stamina_bar_max.bottom = hp_rect.top
    
    display_stamina = max(0, player.stamina_bar)
    stamina_bar_rect = pygame.Rect(stamina_bar_max. left, stamina_bar_max.top, 
                                    stamina_bar_length * (display_stamina / player.config['stamina_max']),
                                    stamina_bar_max.height)

    # Phasing bar update
    phase_bar_length = 500
    phase_bar_max = pygame.Rect(0, 0, phase_bar_length, 20)
    phase_bar_max.centerx = SCREEN_WIDTH//2
    phase_bar_max.centery = SCREEN_HEIGHT - 150

    phase_bar_rect = pygame.Rect(0, phase_bar_max.top,
                                phase_bar_length * (player.phase_bar / player.config['phase_max']), 
                                phase_bar_max.height)
    phase_bar_rect.centerx = phase_bar_max.centerx

    # Draw Player UI
    # STAMINA
    slanted = 10
    color_status = ORANGE if player.stamina_bar > player.config['stamina_max'] / 5 else RED2_0
    if player.is_exhausted: color_status = GREY
    draw_slanted_bar(screen, color_status, stamina_bar_max, slanted)
    if display_stamina > 0: 
        draw_slanted_bar(screen, YELLOW, stamina_bar_rect, slanted)
    draw_slanted_bar(screen, WHITE, stamina_bar_max, slanted, 2)
   
    # PHASE
    if player.phase_bar < player.config['phase_max'] or player.is_exhausted or player.grace_active:
        pygame.draw.rect(screen, FROST_GLOW, phase_bar_max) 
        pygame.draw.rect(screen, ICY_HIGHLIGHT, phase_bar_rect)
        if player.is_exhausted or player.grace_active: pygame.draw.rect(screen, RED2_0, phase_bar_max, 5)
        pygame.draw.rect(screen, WHITE, phase_bar_max, 2)

    # HP
    pygame.draw.rect(screen, BLACK, hp_rect) 
    if player.grace_active: #grace hp
        pygame.draw.rect(screen, RED, (102 + hp_gap, SCREEN_HEIGHT - font_size - 40, player.hp/player.max_hp * 420, 25)) 
        #cur hp
    pygame.draw.rect(screen, GREEN, (102, SCREEN_HEIGHT - font_size - 40, player.hp/player.max_hp * 420, 25))

    #Name 
    p_rect = p_text.get_rect(topleft=(10, SCREEN_HEIGHT - font_size - 10))
    p_rect.width += 17
    draw_slanted_bar(screen, FROST_GLOW, p_rect, slanted)
    draw_slanted_bar(screen, ICY_HIGHLIGHT, p_rect, slanted, 2)
    screen.blit(p_text, (20, SCREEN_HEIGHT - font_size - 10))
    screen.blit(image, player_hp_img_rect)

    #Absorb duration + window max
    icon_rect = pygame.Rect(0, 0, 60, 60)
    icon_rect.midleft = p_rect.midright
    icon_rect.centerx += 10
    icon = get_image(f"cirno/absorb_icon.png", icon_rect)

    counter_font = get_font(24)
    counter_text = counter_font.render(f"Absorbed: {player.absorbed_this_window}/3", True, 
                                        YELLOW if player.absorbed_this_window >= 3 else WHITE)
    counter_rect = counter_text.get_rect(midleft=(icon_rect.right + 8, icon_rect.centery))
    draw_slanted_bar_alpha(screen, (0, 0, 0, 140), counter_rect.inflate(16, 4), 8)

    screen.blit(counter_text, counter_rect)
    screen.blit(icon, icon_rect)
    

    if player.absorb_active:
        progress = min(1.0, player.absorb_timer / player.config['absorb_duration'])
        radial_rect = pygame.Rect(0, 0, 50, 50)
        radial_rect.center = icon_rect.center
        draw_radial_bar(screen, radial_rect, progress, YELLOW, 4)
    
    #Hotbar
    _draw_hotbar(screen, player)
    
    # Boss UI
    boss_counter = 0
    offset = -80
    for b in reversed(stage.boss_list): #read in reverse, so boss1 on top of boss2
        b_text = UI_FONT.render(f"{b.name} (Phase {min(b.current_phase, b.total_phases)}/{b.total_phases})", True, 
                                WHITE if b.alive else RED2_0)
        b_rect = b_text.get_rect(topright=(SCREEN_WIDTH - 40, SCREEN_HEIGHT - font_size - 65 + offset * boss_counter))
        
        
        
        bar_length_max = 500
        bar_length = b.hp / b.max_hp * bar_length_max
        bar_thickness = 20
        bar_rect_max = pygame.Rect(0, 0, bar_length_max, bar_thickness)
        bar_rect_max.top = SCREEN_HEIGHT - font_size - bar_thickness + offset * boss_counter
        bar_rect_max.right = SCREEN_WIDTH - bar_thickness*2

        bar_rect = pygame.Rect(0, bar_rect_max.top, bar_length, bar_thickness)
        bar_rect.right = bar_rect_max.right
        draw_slanted_bar(screen, BLACK, bar_rect_max, -slanted)
        if b.hp > 0:
            draw_slanted_bar(screen, RED2_0, bar_rect, -slanted)
        draw_slanted_bar(screen, WHITE, bar_rect_max, -slanted, 2)

        screen.blit(b_text, b_rect)
        indicator_rect = pygame.Rect(0, 0, bar_thickness, bar_thickness)
        indicator_rect.midright = b_rect.midleft
        indicator_rect.centerx = indicator_rect.centerx - 20
        pygame.draw.rect(screen, b.circle_color, indicator_rect)
        
        boss_counter += 1

def draw_stage_clear(screen, timer_ms):
    alpha = max(0, 255 - int(timer_ms / 3000 * 255))  # fade over 3 seconds
    font = get_font(72)
    text = font.render("STAGE CLEAR!", True, YELLOW)
    text.set_alpha(alpha)
    screen.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3)))

def draw_next_stage_arrow(screen, tick):
    pulse = abs(pygame.math.Vector2(1, 0).x * (tick % 1000 - 500)) / 500  # 0→1→0
    x = int(SCREEN_WIDTH - 175 + pulse * 50)  # bounces right
    y = SCREEN_HEIGHT // 2
    points = [(x, y - 70), (x + 80, y), (x, y + 70)]
    pygame.draw.polygon(screen, YELLOW, points)
    pygame.draw.polygon(screen, WHITE, points, 2)

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

def draw_pause(screen):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 100))
    screen.blit(overlay, (0, 0))
    
    font = get_font(72)
    text = font.render("PAUSED", True, WHITE)
    hint = get_font(28).render("Press ESC to resume", True, GREY)
    
    screen.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40)))
    screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40)))
    