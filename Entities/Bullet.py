from Shared.constants import CYAN, YELLOW, BG_WIDTH, BG_HEIGHT, show_bullet_hitbox
from Entities.GameObject import GameObject

          
class Bullet(GameObject):
    def __init__(self, x, y, vx, vy, hitbox_radius , image="bullet-orb.png", color=CYAN, angle = 0):
        w = h = 2*hitbox_radius
        super().__init__(x, y, w, h, hitbox_radius, f"bullet/{image}", angle=angle)
        self.vx = vx
        self.vy = vy
        self.color = color

    def update(self, dt):
        self.posX += self.vx * dt
        self.posY += self.vy * dt
        self.sync_rect()
        # self.rect.centerx = int(self.posX)
        # self.rect.centery = int(self.posY)

    def draw_self(self, surface):
        super().draw_self(surface)
        if show_bullet_hitbox: self.draw_hitcircle(surface, YELLOW)
        
    def out_of_bounds(self):
        return self.rect.right < -50 or self.rect.left > BG_WIDTH + 50 or self.rect.top > BG_HEIGHT or self.rect.bottom < -50