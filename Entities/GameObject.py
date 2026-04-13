import pygame
from Shared.constants import WHITE, RED, show_img_rect, show_hitbox
from Shared.utils import get_image

class GameObject: #Combination of Circle and Rect hitbox, based on usage (finished?) todo: will probably change if needed
    def __init__ (self, x, y, width = 20, height = 20, hitbox_radius = 15, 
                                                            image_path = None, scale = None,
                                                            flipx = 0, flipy = 0, angle = 0, 
                                                            size_offsetx = 0, size_offsety = 0):
        
        self.hitbox_radius = hitbox_radius
        self.width = width
        self.height = height
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        # self.rect.center = (x, y)
        self.rect.left = x
        self.rect.bottom = y
        self.posX = float(self.rect.x)
        self.posY = float(self.rect.y)
        
        self.image_path = image_path
        self.image = None
        
        if self.image_path: self.image = get_image(image_path, self.rect, scale, flipx, flipy, angle, size_offsetx, size_offsety)
    
    def sync_rect(self):
        self.rect.x = round(self.posX)
        self.rect.y = round(self.posY)

    def draw_self(self, surface):
        if self.image:
            image_rect = self.image.get_rect(center=self.rect.center)
            surface.blit(self.image, image_rect) 
            if show_img_rect: pygame.draw.rect(surface, WHITE, image_rect, 2)
            if show_hitbox: pygame.draw.rect(surface, RED, self.rect, 2) # base hitbox
        else: pygame.draw.rect(surface, WHITE, self.rect, 2) # no texture

    def draw_hitcircle(self, surface, color = WHITE, hitbox_radius = None, border_width = 2): #draw hitbox circle
        hitbox_radius = self.hitbox_radius if hitbox_radius is None else hitbox_radius
        pygame.draw.circle(surface, color, self.rect.center, hitbox_radius, border_width) 
