import math
import random
import pygame
from .config import BLACK, BLUE, DARK_GRAY, DARK_GREEN, GRAY, RED, ROAD_LINE, SKIN, DARK_SKIN, WHITE, YELLOW, PANTS, SHOE


def draw_shadow(surf, x, y, size):
    s = pygame.Surface((size * 2, size // 2), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (0, 0, 0, 45), s.get_rect())
    surf.blit(s, (x - size, y + size - 5))


def person_sprite(body_color, pants_color=PANTS, skin_color=SKIN, accent=None, hat=None, badge=False):
    s = pygame.Surface((42, 42), pygame.SRCALPHA)
    pygame.draw.ellipse(s, pants_color, (8, 14, 18, 6))
    pygame.draw.ellipse(s, pants_color, (8, 22, 18, 6))
    pygame.draw.ellipse(s, SHOE, (5, 13, 8, 7))
    pygame.draw.ellipse(s, SHOE, (5, 22, 8, 7))
    pygame.draw.ellipse(s, body_color, (13, 10, 18, 22))
    pygame.draw.line(s, skin_color, (23, 12), (31, 8), 5)
    pygame.draw.line(s, skin_color, (23, 30), (31, 34), 5)
    pygame.draw.circle(s, skin_color, (32, 21), 7)
    pygame.draw.circle(s, BLACK, (36, 19), 1)
    pygame.draw.circle(s, BLACK, (36, 23), 1)
    if accent:
        pygame.draw.line(s, accent, (17, 16), (26, 16), 2)
        pygame.draw.line(s, accent, (17, 26), (26, 26), 2)
    if hat:
        pygame.draw.ellipse(s, hat, (27, 14, 12, 14), 2)
    if badge:
        pygame.draw.polygon(s, YELLOW, [(22, 18), (25, 21), (22, 24), (19, 21)])
    pygame.draw.ellipse(s, (0, 0, 0, 85), (12, 10, 20, 22), 1)
    return s


def player_sprite():
    return person_sprite((86, 136, 85), accent=YELLOW)


def enemy_sprite():
    return person_sprite((135, 32, 36), pants_color=(25, 25, 34), skin_color=DARK_SKIN, accent=BLACK, hat=BLACK)


def police_sprite():
    return person_sprite((45, 95, 190), pants_color=(20, 30, 70), accent=YELLOW, hat=(20, 50, 135), badge=True)


def civilian_sprite():
    return person_sprite(random.choice([(190, 160, 70), (80, 150, 150), (160, 100, 170), (170, 170, 170), (80, 170, 95)]))


def rotate_draw(surf, sprite, center, angle):
    rotated = pygame.transform.rotate(sprite, -math.degrees(angle))
    surf.blit(rotated, rotated.get_rect(center=center))


def draw_tree(surf, x, y):
    pygame.draw.rect(surf, (90, 62, 38), (x - 3, y, 6, 14))
    pygame.draw.circle(surf, (28, 120, 48), (x, y - 4), 13)
    pygame.draw.circle(surf, (45, 150, 64), (x - 6, y - 8), 8)


def draw_streetlight(surf, x, y, night_alpha=0):
    pygame.draw.rect(surf, DARK_GRAY, (x - 2, y - 18, 4, 22))
    pygame.draw.circle(surf, ROAD_LINE, (x, y - 20), 4)
    if night_alpha:
        light = pygame.Surface((70, 70), pygame.SRCALPHA)
        pygame.draw.circle(light, (255, 230, 120, night_alpha), (35, 35), 35)
        surf.blit(light, (x - 35, y - 55))


def draw_building(surf, building, cam):
    x, y, w, h = building.rect
    sx, sy = int(x - cam[0]), int(y - cam[1])
    c = building.color
    pygame.draw.rect(surf, c, (sx, sy, w, h))
    pygame.draw.rect(surf, BLACK, (sx, sy, w, h), 2)
    if building.kind in ("office", "bank", "apartment"):
        window = (120, 190, 215) if building.kind == "office" else (235, 215, 120)
        for wx in range(sx + 12, sx + w - 8, 24):
            for wy in range(sy + 12, sy + h - 8, 28):
                pygame.draw.rect(surf, window, (wx, wy, 12, 14))
    elif building.kind in ("store", "restaurant", "gas", "gunshop"):
        pygame.draw.rect(surf, (35, 35, 40), (sx + 8, sy + h - 24, w - 16, 18))
        label = building.label[:10]
        font = pygame.font.Font(None, 18)
        txt = font.render(label, True, WHITE)
        surf.blit(txt, (sx + w // 2 - txt.get_width() // 2, sy + 7))
        if building.kind == "gunshop":
            pygame.draw.rect(surf, (165, 42, 42), (sx + 10, sy + 8, w - 20, 18), 2)
            pygame.draw.line(surf, (45, 45, 45), (sx + 24, sy + 40), (sx + w - 24, sy + 40), 4)
    elif building.kind == "factory":
        pygame.draw.rect(surf, GRAY, (sx + w - 18, sy - 28, 12, 30))
    elif building.kind == "villa":
        pygame.draw.rect(surf, (55, 135, 65), (sx - 8, sy - 8, w + 16, h + 16), 2)
        pygame.draw.rect(surf, (130, 55, 45), (sx + w // 2 - 10, sy + h - 18, 20, 18))
    elif building.kind == "police":
        pygame.draw.rect(surf, BLUE, (sx + 8, sy + 8, w - 16, 12))
    elif building.kind == "hospital":
        pygame.draw.rect(surf, WHITE, (sx + w // 2 - 5, sy + 12, 10, 28))
        pygame.draw.rect(surf, RED, (sx + w // 2 - 14, sy + 21, 28, 10))
