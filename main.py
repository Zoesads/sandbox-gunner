import pygame
import time
import math
import json
from random import randint, random
from spritesheet import Spritesheet
from collision import physcmove
from sys import exit

if __name__ == "__main__":

    pygame.font.init()
    pygame.mixer.init()
    pygame.init()

    WIDTH = 700
    HEIGHT = 500
    FPS = 60
    CHUNK_SIZE = 15
    TILE_SIZE = 64

    game_started = False
    Clock = pygame.time.Clock()
    screen = pygame.display.set_mode((WIDTH,HEIGHT),0,16)
    display = pygame.Surface((WIDTH,HEIGHT))
    caption = "Sandbox Gunner"
    tilesheet = Spritesheet(pygame.image.load("graphics/tiles.png").convert_alpha())
    gun = Spritesheet(pygame.image.load("graphics/shotgun.png").convert_alpha())
    particle = Spritesheet(pygame.image.load("graphics/particle.png").convert_alpha())
    tile_offset = {
        1: [0, 0],  2: [1, 0],  3: [2, 0],       4: [4, 0],
        5: [0, 1],  6: [1, 1],  7: [2, 1],       8: [4, 1],
        9: [0, 2], 10: [1, 2], 11: [2, 2],      12: [4, 2],

        13: [0, 4], 14: [1, 4], 15: [2, 4],     16: [4, 4], 17: [5, 4], 18: [6, 4], 19: [7, 4]
    }
    data_file = open("./map.json")
    game_data =  json.load(data_file)['data']
    bigK = len(game_data)-1
    data_file.close()
    map_init = False
    scroll = [0, 0]
    tiles = []
    bullets = []
    efx = []
    chunks = {}
    entities = {}
    player_spawn_loc = [0,0]
    enemy_spawn_loc = []
    game_map_data = game_data[str(randint(0,bigK))]["map"]
    accel = 0.25
    friction = 0.25
    delta = 1
    last_time = time.time()

    walk_audio = pygame.mixer.Sound("audio/walk.wav")
    jump_audio = pygame.mixer.Sound("audio/jump.wav")
    shoot_audio = pygame.mixer.Sound("audio/shoot.wav")
    explosion_audios = [pygame.mixer.Sound("audio/hit.wav"), pygame.mixer.Sound("audio/hit2.wav")]
    ded_audio = pygame.mixer.Sound("audio/die.wav")

    pygame.display.set_caption(caption)
    pygame.display.set_icon(pygame.image.load("graphics/icon.png").convert_alpha())

    walk_audio.set_volume(0.5)
    jump_audio.set_volume(0.5)
    shoot_audio.set_volume(0.5)
    explosion_audios[0].set_volume(0.5)
    explosion_audios[1].set_volume(0.5)
    ded_audio.set_volume(0.5)

    def xypair(x, y):
        return f"{x};{y}"

    def frandom(a, b):
        min_val = min(a, b)
        max_val = max(a, b)
        return min_val + (max_val-min_val)*random()

    def getText(s, size, color=(0, 0, 0)):
        show = pygame.font.Font("graphics/font.ttf", size).render(s, True, color)
        return show

    class Partical:
        def __init__(self, x, y, live_time, typ, data_pack=None):
            self.x = x
            self.y = y
            self.live_time = live_time
            self.typ = typ
            if typ == "p":
                self.size = 5
                self.vx, self.vy, self.size_dec = data_pack

    class Bullet:
        def __init__(self, owner, x, y, vx, vy, rot, isEnemy=False):
            self.sprite = pygame.transform.scale(pygame.image.load("graphics/bullet.png" if not isEnemy else "graphics/enemy_bullet.png").convert_alpha(), (24, 12))
            self.rot = rot
            self.owner = owner
            self.x = x
            self.y = y
            self.vx = vx
            self.vy = vy
            self.live_time = 60
        def get_hitbox(self):
            return pygame.Rect(self.x, self.y, 24, 12)
        def draw(self):
            rot_img = pygame.transform.rotate(self.sprite, self.rot)
            display.blit(rot_img, (self.x+int(rot_img.get_width()/2)-scroll[0], self.y+int(rot_img.get_height()/2)-scroll[1]))

    class Shotgun:
        def __init__(self, owner, isEnemy = False):
            self.spritesheet = Spritesheet(pygame.image.load("graphics/shotgun.png" if not isEnemy else "graphics/enemy_shotgun.png").convert_alpha())
            self.left = self.spritesheet.getsprite(12, 4, 0, 0, 3, 3)
            self.right = self.spritesheet.getsprite(12, 4, 1, 0, 3, 3)
            self.sprite = self.left
            self.rot = 0
            self.owner = owner
        def update(self, px, py):
            n = len(bullets)
            i = 0
            collision_counter = False
            while i < n:
                bullet = bullets[i]
                if bullet.owner == self.owner:
                    bullet.live_time -= 1

                    hitbox = bullet.get_hitbox()
                    bullet.x += bullet.vx
                    bullet.y += bullet.vy

                    collided = [rect for rect in tiles if hitbox.colliderect(rect)]
                    collision_count = len(collided)

                    entity_collided = [ent for ent in entities.keys() if hitbox.colliderect(ent.get_hitbox()) and self.owner != ent and self.owner.team != ent.team]
                    entity_collision_count = len(entity_collided)

                    bullet_collided = [b for b in bullets if hitbox.colliderect(b.get_hitbox()) and self.owner != b.owner]
                    bullet_collision_count = len(bullet_collided)

                    col_x, col_y = bullet.x, bullet.y

                    A = -1
                    B = -1
                    C = -1
                    D = -1

                    if bullet_collision_count == 0:
                        if entity_collision_count == 0:
                            if collision_count == 0:
                                bullet.draw()
                            else:
                                collision_counter = True
                                A, C = collided[0].x, collided[0].y
                                B, D = bullet.x, bullet.y
                        else:
                            collision_counter = True
                            A, C = entity_collided[0].x, entity_collided[0].y
                            B, D = bullet.x, bullet.y
                            entity_collided[0].died = True
                            entities.pop(entity_collided[0])
                    else:
                        collision_counter = True
                        A, C = bullet_collided[0].x, bullet_collided[0].y
                        B, D = bullet.x, bullet.y
                        ded_audio.play()
                        
                    if A != -1 and B != -1 and C != -1 and D != -1:
                        angle = int(math.degrees(math.atan2(A-B, C-D)))
                        angle = math.radians((360 if angle < 0 else 0) - angle)
                        for z in range(30):
                            r = frandom(-10,10)
                            theta = math.radians(-((360 if (angle+r) < 0 else 0) - (angle+r)))
                            efx.append(Partical(col_x,col_y,randint(30,45),"p", (frandom(1,8)*(1 if col_x < px else -1)*math.cos(theta), 22*(1 if py > col_y else -1)*math.sin(theta), frandom(0.005, 0.01))))
                if collision_counter or bullets[i].live_time <= 0:
                    i -= 1
                    n -= 1
                    bullets.pop(i)
                    if collision_counter:
                        explosion_audios[randint(0,1)].play()
                i += 1


    class Player:
        def __init__(self):
            entities[self] = self
            self.team = 0
            self.spritesheet = Spritesheet(pygame.image.load("graphics/player.png").convert_alpha())
            self.sprite = self.spritesheet.getsprite(8, 16, 0, 0, 3, 3)
            self.gun = Shotgun(self)
            self.status = "idle"
            self.frame = [0, 0, 2, 0.05]
            self.w = 24
            self.h = 48
            self.died = False
            self.moving_left = False
            self.moving_right = False
            self.x = player_spawn_loc[0]
            self.y = player_spawn_loc[1]
            self.vx = 0
            self.jumpable = True
            self.jump_cd = 0
            self.walk_aud_cd = 0
            self.vy = 0
            self.eyes_offset = [6, 13]
            self.gun_offset = [10, 25, 1]
            self.eyes_pos = [[0, 0],[0, 0]]
            self.gun_pos = [0, 0]
        def get_hitbox(self):
            return pygame.Rect(self.x, self.y, self.w, self.h)
        def update(self):
            if self.died: return
            self.jump_cd -= 0.195

            # get mouse current position
            mx, my = pygame.mouse.get_pos()

            # check facing
            A, B = self.x-scroll[0], self.y-scroll[1]
            angle = int(math.degrees(math.atan2(A-mx,B-my)))
            if angle >= 0:
                self.eyes_offset = [6, 13]
                self.gun_offset = [8, 26, 0]
                self.gun_offset[2] = 1
                self.gun_sprite = gun.getsprite(8, 4, 0, 0, 3, 3)
                self.gun.sprite = self.gun.left
            else:
                self.eyes_offset = [14, 7.25]
                self.gun_offset = [15, 26, 0]
                self.gun_offset[2] = -1
                self.gun.sprite = self.gun.right

            # movement handle
            collided = physcmove(self, self.vx*delta, self.vy*delta, tiles)
            if not collided['bottom']:
                self.vy += accel
            else:
                self.vy = 0
                self.jumpable = True
                if int(self.vx)!= 0 and not collided['left'] and not collided['right']:
                    self.walk_aud_cd -= 0.2
                    if self.walk_aud_cd <= 0:
                        walk_audio.play()
                        self.walk_aud_cd = 0.4
            if collided['top']:
                self.vy = 1
            if collided['right'] or collided['left']:
                if not collided['bottom']:
                    self.jumpable = True

            # friction after fall
            if self.vx > 0 and not self.moving_right:
                self.vx = max(self.vx-friction, 0)
            elif self.vx < 0 and not self.moving_left:
                self.vx = min(self.vx+friction, 0)

            # get current frame
            cur_frame = int(self.frame[0])

            # move eyes
            eye_height_offset = self.y + (8 if cur_frame != 1 else 10)
            self.eyes_pos[0] = [self.x+self.eyes_offset[0],eye_height_offset]
            self.eyes_pos[1] = [self.x+self.eyes_offset[1],eye_height_offset]

            # move gun
            gun_height_offset = self.y + self.gun_offset[1] + (4 if cur_frame == 1 else 0)
            gx, gy = self.gun_pos[0]-scroll[0], self.gun_pos[1]-scroll[1]
            angle = int(math.degrees(math.atan2(gy-my,gx-mx) if self.gun_offset[2] == 1 else math.atan2(my-gy,mx-gx)))
            angle = (360 if angle < 0 else 0) - angle
            self.gun.rot = angle
            self.gun_pos =  [self.x+self.gun_offset[0],gun_height_offset]

            # update sprite
            self.sprite = self.spritesheet.getsprite(8, 16, cur_frame, 0, 3, 3)
            self.frame[0] += self.frame[3]
            if self.frame[3] > 0 and self.frame[0] > self.frame[2] or self.frame[3] < 0 and self.frame[0] < self.frame[2] or self.frame[0] == self.frame[2]:
                self.frame[0] = self.frame[1]

        def fire(self):
            if self.died: return
            mx, my = pygame.mouse.get_pos()
            angle = int(math.degrees(math.atan2(my-self.gun_pos[1]+scroll[1],mx-self.gun_pos[0]+scroll[0])))
            shoot_audio.play()
            for i in range(-10, 11, 10):
                theta = math.radians(-((360 if (angle-i) < 0 else 0) - (angle-i)))
                bullet_speed = 20
                bullets.append(Bullet(self, self.gun_pos[0]+(-18 if int(self.gun_offset[2]==1) else -2), self.gun_pos[1] - 12, bullet_speed*math.cos(theta), bullet_speed*math.sin(theta), self.gun.rot))
            angle = math.radians(-((360 if angle < 0 else 0) - angle))
            self.vx = -22*math.cos(angle)
            self.vy = -10*math.sin(angle)

        def draw(self):
            if self.died: return
            display.blit(self.sprite,(self.x-scroll[0],self.y-scroll[1]))
            rotated_gun = pygame.transform.rotate(self.gun.sprite, self.gun.rot)
            display.blit(rotated_gun, (self.gun_pos[0]-scroll[0]-int(rotated_gun.get_width()/2), self.gun_pos[1]-scroll[1]-int(rotated_gun.get_height()/2)))
            self.gun.update(self.x, self.y)
            for pos in self.eyes_pos:
                px, py = [pos[0]-scroll[0], pos[1]-scroll[1]]
                pygame.draw.rect(display, (28, 28, 28), (px, py, 4, 4))
                
    class Enemy:
        def __init__(self, x, y):
            entities[self] = self
            self.team = 1
            self.sprite = pygame.transform.scale(pygame.image.load("graphics/enemy.png").convert_alpha(), (24, 48))
            self.gun = Shotgun(self, True)
            self.died = False
            self.w = 24
            self.h = 48
            self.x = x
            self.y = y
            self.shoot_cd = 0
            self.eyes_offset = [6, 13]
            self.gun_offset = [10, 25, 1]
            self.eyes_pos = [[0, 0],[0, 0]]
            self.gun_pos = [0, 0]

        def get_hitbox(self):
            return pygame.Rect(self.x, self.y, self.w, self.h)
        def update(self):
            if self.died: return
            self.shoot_cd -= 0.2

            # get player position
            px, py = plr.x-scroll[0], plr.y-scroll[1]

            # check facing
            A, B = self.x-scroll[0], self.y-scroll[1]
            angle = -int(math.degrees(math.atan2(px-A,py-B)))
            if angle >= 0:
                self.eyes_offset = [6, 13]
                self.gun_offset = [8, 26, 0]
                self.gun_offset[2] = 1
                self.gun_sprite = gun.getsprite(8, 4, 0, 0, 3, 3)
                self.gun.sprite = self.gun.left
            else:
                self.eyes_offset = [14, 7.25]
                self.gun_offset = [15, 26, 0]
                self.gun_offset[2] = -1
                self.gun.sprite = self.gun.right

            # move eyes
            eye_height_offset = self.y + 8
            self.eyes_pos[0] = [self.x+self.eyes_offset[0],eye_height_offset]
            self.eyes_pos[1] = [self.x+self.eyes_offset[1],eye_height_offset]

            # move gun
            gun_height_offset = self.y + self.gun_offset[1]
            gx, gy = self.gun_pos[0]-scroll[0], self.gun_pos[1]-scroll[1]
            angle = int(math.degrees(math.atan2(gy-px,gx-py) if self.gun_offset[2] == 1 else math.atan2(py-gy,px-gx)))
            angle = (360 if angle < 0 else 0) - angle
            self.gun.rot = angle
            self.gun_pos =  [self.x+self.gun_offset[0],gun_height_offset]

            # check if can shoot
            dist = abs((pow(px - enemy.x + scroll[0],2)+pow(py - enemy.y + scroll[1],2))**0.5)
            if dist < 250 and self.shoot_cd <= 0:
                self.fire()
                self.shoot_cd = 5

        def fire(self):
            if self.died: return
            A, B = plr.x, plr.y
            angle = int(math.degrees(math.atan2(self.gun_pos[1]-B,self.gun_pos[0]-A)))
            bullet_speed = 10
            shoot_audio.play()
            for z in range(-10, 11, 20):
                theta = math.radians(-((360 if (angle-z) < 0 else 0) - (angle-z) - 5))
                bullets.append(Bullet(self, self.gun_pos[0]+(-18 if int(self.gun_offset[2]==1) else -2), self.gun_pos[1] - 25, -bullet_speed*math.cos(theta), -bullet_speed*math.sin(theta), self.gun.rot, True))

        def draw(self):
            if self.died: return
            display.blit(self.sprite,(self.x-scroll[0],self.y-scroll[1]))
            rotated_gun = pygame.transform.rotate(self.gun.sprite, self.gun.rot)
            display.blit(rotated_gun, (self.gun_pos[0]-scroll[0]-int(rotated_gun.get_width()/2), self.gun_pos[1]-scroll[1]-int(rotated_gun.get_height()/2)))
            self.gun.update(self.x, self.y)
            for pos in self.eyes_pos:
                px, py = [pos[0]-scroll[0], pos[1]-scroll[1]]
                pygame.draw.rect(display, (28, 28, 28), (px, py, 4, 4))
    
    def load_box():
        global enemy_spawn_loc, player_spawn_loc, chunks, game_init, scroll, tiles, bullets, efx, chunks, entities, player_spawn_loc, enemy_spawn_loc, game_map_data, plr, enemies
        map_init = False
        scroll = [0, 0]
        tiles = []
        bullets = []
        efx = []
        chunks = {}
        entities = {}
        player_spawn_loc = [0,0]
        enemy_spawn_loc = []
        game_map_data = game_data[str(randint(0,bigK))]["map"]
        for y, row in enumerate(game_map_data):
            for x, val in enumerate(row):
                if val < 1:
                    if val == -1:
                        player_spawn_loc = [x * TILE_SIZE, y * TILE_SIZE]
                    elif val == -2:
                        enemy_spawn_loc.append([x*TILE_SIZE, y*TILE_SIZE])
                    continue
                if not map_init:
                    r = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    tiles.append(r)

        for y in range(0,30,CHUNK_SIZE):
            row = game_map_data[y:y+CHUNK_SIZE]
            for x in range(0,30,CHUNK_SIZE):
                chunk_data = []
                tiles_in_range = [r[x:x+CHUNK_SIZE] for r in row]
                for tile_y in range(CHUNK_SIZE):
                    for tile_x in range(CHUNK_SIZE):
                        val = tiles_in_range[tile_y][tile_x]
                        if val < 1:
                            continue
                        ox, oy = tile_offset[val]
                        chunk_data.append([tilesheet.getsprite(16, 16, ox, oy, 4, 4),((x+tile_x)*TILE_SIZE,(y+tile_y)*TILE_SIZE)])
                if len(chunk_data) > 0:
                    chunks[xypair(int(x/CHUNK_SIZE), int(y/CHUNK_SIZE))] = chunk_data
        plr = Player()
        enemies = []
        for loc in enemy_spawn_loc:
            enemies.append(Enemy(loc[0],loc[1]+16))
    plr = None
    enemies = []
    while True:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
                key = pygame.key.get_pressed()
                if game_started:
                    if key[pygame.K_SPACE] and plr.jumpable and plr.jump_cd <= 0:
                        plr.frame = [4, 4, 5, 1]
                        plr.vy = -5
                        plr.jump_cd = 5
                        plr.jumpable = False
                        jump_audio.play()
                    if key[pygame.K_a]:
                        if plr.jumpable:
                            plr.frame = [2, 2, 4, 0.1]
                        plr.vx = -5
                        plr.moving_left = True
                    else:
                        plr.moving_left = False
                    if key[pygame.K_d]:
                        if plr.jumpable:
                            plr.frame = [3, 3.9, 2, -0.1]
                        plr.vx = 5
                        plr.moving_right = True
                    else:
                        plr.moving_right = False
                    if not key[pygame.K_a] and not key[pygame.K_d]:
                        plr.frame = [0, 0, 2, 0.05]
                else:
                    if key[pygame.K_RETURN]:
                        game_started = True
                        load_box()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse = pygame.mouse.get_pressed()
                if mouse[0]:
                    if game_started:
                        plr.fire()
                
        display.fill((225,225,225))

        if game_started:

            scroll[0] += int((plr.x-scroll[0]-350+plr.w)/2)
            scroll[1] += int((plr.y-scroll[1]-250+plr.h)/2)
            
            delta = (time.time()-last_time)*60
            last_time = time.time()

            for y in range(round(HEIGHT/CHUNK_SIZE)):
                for x in range(round(WIDTH/CHUNK_SIZE)):
                    targ_x = abs(x - 1 + round(scroll[0]/(CHUNK_SIZE*TILE_SIZE)))
                    targ_y = abs(y - 1 + round(scroll[1]/(CHUNK_SIZE*TILE_SIZE)))
                    targ_chunk = xypair(targ_x, targ_y)
                    if targ_chunk in chunks:
                        for tile in chunks[targ_chunk]:
                            display.blit(tile[0],(tile[1][0]-scroll[0],tile[1][1]-scroll[1]))

            map_init = True
            plr.update()
            plr.draw()
            for enemy in enemies:
                enemy.update()
                enemy.draw()

            efx_index = 0
            n = len(efx)
            while efx_index < n:
                effect = efx[efx_index]
                if effect.typ == "p":
                    p_pos = int(5-effect.size)
                    scale = 8
                    img = particle.getsprite(5, 5, p_pos, 0, scale, scale)
                    display.blit(img, (effect.x-scroll[0]+p_pos*scale,effect.y-scroll[1]+p_pos*scale))
                    effect.size -= 0.2
                    effect.size = max(effect.size,0)
                    effect.x += effect.vx
                    effect.y += effect.vy
                effect.live_time -= 1
                if effect.live_time < 1:
                    efx.pop(efx_index)
                    efx_index -= 1
                    n -= 1
                efx_index += 1

            if plr.died or len(entities) == 1 or plr.y >=  12000:
                load_box()
        else:
            display.blit(getText("Sandbox", 100, (14, 14, 14)), (WIDTH/2-130, HEIGHT/2-145))
            display.blit(getText("Sandbox", 100, (252, 185, 28)), (WIDTH/2-130, HEIGHT/2-150))

            display.blit(getText("Gunner", 125, (14, 14, 14)), (WIDTH/2-135, HEIGHT/2-95))
            display.blit(getText("Gunner", 125, (56, 129, 255)), (WIDTH/2-135, HEIGHT/2-100))

            display.blit(getText("Press Enter to start", 35, (23, 23, 23)), (WIDTH/2-128, HEIGHT/2))

        screen.blit(display, (0, 0))

        pygame.display.update()
        Clock.tick(FPS)
