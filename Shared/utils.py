import pygame, json, math

def load_json(path):
    with open(f"data/{path}", "r") as f:
        data = json.load(f)
    return data

def get_end_pos(x, y, angle, length): # for line might delete later, after getting a texture for facing indicator
    end_x = x + length * math.cos(angle)
    end_y = y + length * math.sin(angle)
    return (end_x, end_y)

def circle_collide(c1_pos, r1, c2_pos, r2):
    dx = c1_pos[0] - c2_pos[0] 
    dy = c1_pos[1] - c2_pos[1]
    return dx*dx + dy*dy <= (r1 + r2) ** 2 # dx^2 + dy^2 <= (r_1 + r_2)^2 rumus kolisi lingkaran

assets = {} 
def load_asset(image_path): #load base image into cache
    path = "assets/" + image_path
    if path not in assets:
        assets[path] = pygame.image.load(path).convert_alpha()
    return assets[path]

image_cache = {} 
def get_image(image_path, rect=None, # load or make a new image in cache (into the assigned rectangle if available)
               flipx = 0, flipy = 0, angle = 0, 
               size_offsetx = 0, size_offsety = 0): # offset for minor adjustment, not needed if image is edited on figma
    scale = None
    if rect: 
        scale = (rect.width + size_offsetx, rect.height + size_offsety) #size based on rect
    elif size_offsetx or size_offsety: 
        scale = (size_offsetx, size_offsety) # size only

    key = (image_path, scale, flipx, flipy, angle)
 
    if key not in image_cache:
        image = load_asset(image_path)
        image = pygame.transform.flip(image, flipx, flipy)
        if scale: image = pygame.transform.scale(image, scale)
        image = pygame.transform.rotate(image, angle)
        image_cache[key] = image
    return image_cache[key]
