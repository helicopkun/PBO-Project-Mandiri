from Entities.GameObject import GameObject
from Shared.constants import*
          
class Bullet(GameObject):
    def __init__(self, x, y, vx, vy, hitbox_radius , image="bullet-orb.png", color=CYAN, #default
                                                                 flipx = 0, flipy = 0, angle = 0, 
                                                                 size_offsetx=60, size_offsety=32.5):
        w = h = 2*hitbox_radius
        super().__init__(x, y, w, h, hitbox_radius, f"bullet/{image}", flipx, flipy, angle, size_offsetx, size_offsety)
        self.vx = vx
        self.vy = vy
        self.color = color

    def update(self, dt):
        self.rect.centerx += self.vx * dt
        self.rect.centery += self.vy * dt
        
    def out_of_bounds(self):
        return self.rect.right < -50 or self.rect.left > WIDTH + 50 or self.rect.top > HEIGHT or self.rect.bottom < -50
