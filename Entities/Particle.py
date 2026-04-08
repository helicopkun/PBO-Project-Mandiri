import pygame, random, math

class Particle:
    def __init__(self, x, y, color, is_burst=False):
        self.x = x
        self.y = y
        self.color = color
        self.size = random.uniform(8, 16)
        self.lifetime = random.uniform(0.2, 0.5)
        self.max_lifetime = self.lifetime
        
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(150, 400) if is_burst else random.uniform(50, 150) # make them shoot out faster
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.lifetime -= dt

    def draw(self, surface):
        if self.lifetime > 0:
            current_size = max(0.1, self.size * (self.lifetime / self.max_lifetime)) # Slowly shrink
            pygame.draw.rect(surface, self.color, (self.x, self.y, current_size, current_size))

def spawn_particles(x, y, color, particles_list, count=5, is_burst=False):
    for i in range(count):
        particles_list.append(Particle(x, y, color, is_burst))