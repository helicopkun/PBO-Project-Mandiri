import pygame, json, math, os

def load_json(path):
    with open(f"data/{path}", "r") as f:
        data = json.load(f)
    return data

def draw_radial_bar(surface, rect, progress, color, width=5):
    # progress = 1.0 full, 0.0 empty
    start_angle = math.pi / 2
    end_angle = math.pi / 2 + (2 * math.pi * progress)

    pygame.draw.arc(surface, color, rect, start_angle, end_angle, width)

def draw_slanted_bar(surface, color, rect, offset, width = 0):
    x, y, w, h = rect
    if w <= offset: return
    points = [
        (x + offset, y),
        (x + w, y),
        (x + w - offset, y + h),
        (x, y + h)
    ]
    pygame.draw.polygon(surface, color, points, width) #paints inside canvas

def draw_slanted_bar_alpha(surface, color, rect, offset, width=0):
    x, y, w, h = rect
    if w <= offset: return
    points = [
        (offset,      0),  # top left
        (w,           0),  # top right
        (w - offset,  h),  # bottom right
        (0,           h)   # bottom left
    ]
    temp = pygame.Surface((w + offset, h), pygame.SRCALPHA) #make new canvas
    pygame.draw.polygon(temp, color, points, width) #paint into new canvas
    surface.blit(temp, (x, y)) #add canvas to canvas

def circle_collide(c1_pos, r1, c2_pos, r2):
    dx = c1_pos[0] - c2_pos[0] 
    dy = c1_pos[1] - c2_pos[1]
    return dx*dx + dy*dy <= (r1 + r2) ** 2 # dx^2 + dy^2 <= (r_1 + r_2)^2 rumus kolisi lingkaran

base_img = {}   
def _load_base_img(image_path): #load base image into cache
    path = "assets/" + image_path
    if path not in base_img:
        base_img[path] = pygame.image.load(path).convert_alpha()
    return base_img[path]

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
        image = _load_base_img(image_path)
        image = pygame.transform.flip(image, flipx, flipy)
        if size: image = pygame.transform.scale(image, size)
        if scale: image = pygame.transform.scale_by(image, scale)
        image = pygame.transform.rotate(image, angle)
        image_cache[key] = image
    return image_cache[key]

sound_cache = {}
def get_sound(path):
    if path not in sound_cache:
        sound_cache[path] = pygame.mixer.Sound(f"assets/sfx/{path}")
    return sound_cache[path]

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