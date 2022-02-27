import pygame

def physcmove(rect, velocity_x, velocity_y, tiles):
    def test(a, b):
        return [c for c in b if a.colliderect(c)]
    types = {
        'top': False,
        'left': False,
        'right': False,
        'bottom': False
    }
    temp_rect = pygame.Rect(rect.x, rect.y, rect.w, rect.h)
    temp_rect.x += velocity_x
    for r in test(temp_rect, tiles):
        if velocity_x > 0:
            temp_rect.right = r.left
            types['right'] = True
        elif velocity_x < 0:
            temp_rect.left = r.right
            types['left'] = True

    temp_rect.y += velocity_y
    for r in test(temp_rect, tiles):
        if velocity_y > 0:
            temp_rect.bottom = r.top
            types['bottom'] = True
        elif velocity_y < 0:
            temp_rect.top = r.bottom
            types['top'] = True

    rect.y = temp_rect.y
    rect.x = temp_rect.x

    return types
    