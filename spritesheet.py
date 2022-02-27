import pygame

class Spritesheet:
    def __init__(self, sheet):
        self.sheet = sheet
    def getsprite(self, sx_spr, sy_spr, pos_x=0, pos_y=0, scale_x=1, scale_y=1):
        w, h = self.sheet.get_size()
        sx = sx_spr * scale_x
        sy = sy_spr * scale_y
        surf = pygame.Surface((sx, sy))
        surf.set_colorkey((0,0,0))
        surf.blit(pygame.transform.scale(self.sheet, (w * scale_x, h * scale_y)), (sx * -pos_x, sy * -pos_y))
        return surf