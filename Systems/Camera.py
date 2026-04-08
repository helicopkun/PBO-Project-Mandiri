import pygame, random
from Shared.constants import SCREEN_WIDTH, SCREEN_HEIGHT, BG_WIDTH, BG_WIDTH, BG_HEIGHT, BG_BORDER_X
class Camera:
    def __init__(self, player):
        self.offset_x = 0
        self.offset_y = 0
        self.shake_timer = 0
        self.player = player

    def update(self, dt):
        self._update_follow()
        self._update_shake(dt)

    def _update_follow(self):
        margin = 200
        target_x = -175
        target_y = 0

        if self.player.rect.left > SCREEN_WIDTH - margin + BG_BORDER_X:
            target_x = -(self.player.rect.right - (SCREEN_WIDTH - margin))
        elif self.player.rect.right < margin + BG_BORDER_X:
            target_x = margin - self.player.rect.left

        if self.player.rect.bottom > SCREEN_HEIGHT - margin:
            target_y = -(self.player.rect.bottom - (SCREEN_HEIGHT - margin))

        max_scroll_x = -(BG_WIDTH - SCREEN_WIDTH)   # = -400
        max_scroll_y = -(BG_HEIGHT - SCREEN_HEIGHT)  # = -200
        target_x = max(max_scroll_x, min(0, target_x))
        target_y = max(max_scroll_y, min(0, target_y))

        self.offset_x += (target_x - self.offset_x) * 0.1
        self.offset_y += (target_y - self.offset_y) * 0.1

    def _update_shake(self, dt):
        if self.shake_timer > 0:
            self.shake_timer -= dt

    def trigger_shake(self, duration=0.25):
        self.shake_timer = duration

    def get_offset(self):
        shake_x, shake_y = 0, 0
        if self.shake_timer > 0:
            intensity = 8
            shake_x = random.randint(-intensity, intensity)
            shake_y = random.randint(-intensity, intensity)
        return int(self.offset_x + shake_x), int(self.offset_y + shake_y)