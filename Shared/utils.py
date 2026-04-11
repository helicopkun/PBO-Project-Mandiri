import pygame, json, math, os

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
def _load_asset(image_path): #load base image into cache
    path = "assets/" + image_path
    if path not in assets:
        assets[path] = pygame.image.load(path).convert_alpha()
    return assets[path]

image_cache = {} 
def get_image(image_path, rect=None, scale = None, # load or make a new image in cache (into the assigned rectangle if available)
               flipx = 0, flipy = 0, angle = 0, 
               size_offsetx = 0, size_offsety = 0): # offset for minor adjustment, not needed if image is edited on figma
    size = None
    if rect: 
        size = (rect.width + size_offsetx, rect.height + size_offsety) #size based on rect
    elif size_offsetx or size_offsety: 
        size = (size_offsetx, size_offsety) # size only

    key = (image_path, size, scale, flipx, flipy, angle)
 
    if key not in image_cache:
        image = _load_asset(image_path)
        image = pygame.transform.flip(image, flipx, flipy)
        if size: image = pygame.transform.scale(image, size)
        if scale: image = pygame.transform.scale_by(image, scale)
        image = pygame.transform.rotate(image, angle)
        image_cache[key] = image
    return image_cache[key]

def preload_assets(atk_data): #preload same image, but multiple variation
    # Character states
    for state in os.listdir("assets/cirno"):
        for flip in [0, 1]:
            get_image(f"cirno/{state}", flipx=flip)

    # Attack images - all angles x all frames
    for attack_type in os.listdir("assets/attack"):
        for filename in os.listdir(f"assets/attack/{attack_type}"):
            for deg in range(0, 360, 15):
                get_image(f"attack/{attack_type}/{filename}", angle=deg, 
                          scale=atk_data[str(attack_type)]['scale'])

    # Bullet images
    for bullet in os.listdir("assets/bullet"):
        for deg in range(0, 360, 5):
            get_image(f"bullet/{bullet}", angle=deg)

def update_animation(surface, cur_img, center, total_frame, cur_frame, duration, timestamp):
    if cur_frame >= total_frame: return total_frame, 0
    
    img_rect = cur_img.get_rect(center=center)
    surface.blit(cur_img, img_rect)

    frame_delay = duration*1000 / total_frame # i put it here so frame 0 can still play
    if pygame.time.get_ticks() - timestamp > frame_delay:
        timestamp = pygame.time.get_ticks()
        cur_frame += 1
    
    return cur_frame, timestamp