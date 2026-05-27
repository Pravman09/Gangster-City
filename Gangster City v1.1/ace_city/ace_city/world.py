import random
import pygame
from .config import CHUNK_SIZE, DARK_GREEN, MAP_H, MAP_W, ROAD, ROAD_LINE, SIDEWALK, WATER
from .utils import rects_overlap, on_screen_rect
from .sprites import draw_building, draw_tree, draw_streetlight


class Building:
    def __init__(self, rect, kind, color, district, label=""):
        self.rect = rect
        self.kind = kind
        self.color = color
        self.district = district
        self.label = label or kind.upper()


class District:
    def __init__(self, name, rect, ground, building_kinds, palette, atmosphere):
        self.name = name
        self.rect = rect
        self.ground = ground
        self.building_kinds = building_kinds
        self.palette = palette
        self.atmosphere = atmosphere


class City:
    def __init__(self):
        self.roads = []
        self.sidewalks = []
        self.highways = []
        self.alleys = []
        self.buildings = []
        self.decorations = []
        self.landmarks = []
        self.districts = self.make_districts()
        self.generate_roads()
        self.generate_buildings()
        self.generate_decorations()

    def make_districts(self):
        return [
            District("Downtown", (3300, 2200, 2300, 1700), (36, 45, 52),
                     ["office", "bank", "apartment"], [(70, 95, 115), (55, 80, 100), (90, 120, 135)], "glass towers"),
            District("Slums", (400, 4300, 2300, 1900), (64, 55, 45),
                     ["slum", "store", "garage"], [(115, 82, 58), (92, 70, 55), (135, 95, 60)], "dirty roads"),
            District("Rich Hills", (6200, 380, 2500, 1700), (35, 95, 55),
                     ["villa", "store"], [(215, 198, 160), (190, 170, 135), (230, 220, 180)], "villas and gardens"),
            District("Industrial", (6200, 4400, 2600, 2000), (70, 66, 58),
                     ["factory", "warehouse", "garage"], [(95, 92, 86), (125, 112, 90), (80, 86, 90)], "warehouses and smoke"),
            District("Market Mile", (850, 900, 2200, 1800), (55, 65, 70),
                     ["store", "restaurant", "gas", "apartment"], [(130, 80, 95), (70, 120, 150), (160, 125, 70)], "shops and neon"),
            District("Civic Center", (3600, 4500, 1700, 1600), (44, 78, 70),
                     ["police", "hospital", "bank", "apartment"], [(80, 120, 165), (215, 215, 210), (145, 125, 95)], "services"),
            District("Green Park", (3600, 600, 1600, 1200), (32, 118, 58),
                     ["landmark"], [(60, 145, 70)], "trees and benches"),
        ]

    def generate_roads(self):
        road_w = 96
        for x in range(520, MAP_W, 720):
            self.roads.append((x - road_w // 2, 0, road_w, MAP_H))
        for y in range(460, MAP_H, 680):
            self.roads.append((0, y - road_w // 2, MAP_W, road_w))
        self.highways.append((0, 3350, MAP_W, 150))
        self.highways.append((5450, 0, 150, MAP_H))
        self.roads.extend(self.highways)
        for x, y, w, h in self.roads:
            self.sidewalks.append((x - 20, y - 20, w + 40, h + 40))
        for x in range(260, MAP_W, 720):
            self.alleys.append((x, 0, 32, MAP_H))

    def district_at(self, x, y):
        for d in self.districts:
            if rects_overlap((x, y, 1, 1), d.rect):
                return d
        return District("Outskirts", (0, 0, MAP_W, MAP_H), DARK_GREEN,
                        ["slum", "store", "warehouse"], [(95, 85, 65), (75, 95, 75)], "mixed")

    def generate_buildings(self):
        special = [
            ((4080, 5000, 260, 180), "police", (70, 110, 175), "Civic Center", "POLICE HQ"),
            ((4550, 5050, 250, 170), "hospital", (222, 222, 216), "Civic Center", "HOSPITAL"),
            ((4200, 2700, 300, 220), "bank", (125, 112, 82), "Downtown", "BANK"),
            ((1500, 1450, 210, 150), "gas", (190, 55, 45), "Market Mile", "GAS"),
            ((7050, 1200, 240, 190), "villa", (220, 205, 170), "Rich Hills", "MANSION"),
            ((7050, 5100, 360, 240), "factory", (100, 100, 95), "Industrial", "STEELWORKS"),
            ((4000, 880, 260, 180), "landmark", (70, 150, 75), "Green Park", "CITY PARK"),
            ((2380, 1900, 230, 160), "garage", (95, 90, 85), "Market Mile", "GARAGE"),
        ]
        for rect, kind, color, district, label in special:
            self.buildings.append(Building(rect, kind, color, district, label))
            self.landmarks.append(self.buildings[-1])

        attempts = 0
        while len(self.buildings) < 580 and attempts < 25000:
            attempts += 1
            d = random.choice(self.districts)
            dx, dy, dw, dh = d.rect
            if d.name == "Green Park" and random.random() < 0.85:
                continue
            w = random.randint(80, 210)
            h = random.randint(70, 190)
            if d.name == "Downtown":
                w, h = random.randint(110, 260), random.randint(160, 340)
            if d.name == "Industrial":
                w, h = random.randint(180, 360), random.randint(120, 280)
            x = random.randint(dx + 20, dx + dw - w - 20)
            y = random.randint(dy + 20, dy + dh - h - 20)
            rect = (x, y, w, h)
            if any(rects_overlap(rect, road, 28) for road in self.roads):
                continue
            if any(rects_overlap(rect, b.rect, 22) for b in self.buildings):
                continue
            kind = random.choice(d.building_kinds)
            color = random.choice(d.palette)
            label = random.choice(["SHOP", "CAFE", "MART", "FOOD"]) if kind in ("store", "restaurant") else kind.upper()
            self.buildings.append(Building(rect, kind, color, d.name, label))

    def generate_decorations(self):
        for _ in range(850):
            d = random.choice(self.districts)
            x = random.randint(d.rect[0], d.rect[0] + d.rect[2])
            y = random.randint(d.rect[1], d.rect[1] + d.rect[3])
            if any(rects_overlap((x - 8, y - 8, 16, 16), b.rect, 6) for b in self.buildings):
                continue
            if d.name in ("Green Park", "Rich Hills"):
                self.decorations.append(("tree", x, y))
            elif random.random() < 0.35:
                self.decorations.append(("light", x, y))
            else:
                self.decorations.append(("bench", x, y))

        for b in self.buildings:
            if b.kind == "factory":
                x, y, w, _ = b.rect
                self.decorations.append(("smoke", x + w - 15, y - 30))

    def collision_rects_near(self, pos, radius=260):
        px, py = pos
        area = (px - radius, py - radius, radius * 2, radius * 2)
        return [b.rect for b in self.buildings if rects_overlap(area, b.rect)]

    def random_open_position(self, margin=120, radius=20, district_name=None):
        for _ in range(1500):
            if district_name:
                d = next((d for d in self.districts if d.name == district_name), None)
                x = random.randint(d.rect[0] + margin, d.rect[0] + d.rect[2] - margin)
                y = random.randint(d.rect[1] + margin, d.rect[1] + d.rect[3] - margin)
            else:
                x = random.randint(margin, MAP_W - margin)
                y = random.randint(margin, MAP_H - margin)
            r = (x - radius, y - radius, radius * 2, radius * 2)
            if any(rects_overlap(r, b.rect, 10) for b in self.buildings):
                continue
            return x, y
        return MAP_W // 2, MAP_H // 2

    def draw_ground(self, surf, cam, screen_w, screen_h):
        surf.fill(DARK_GREEN)
        for d in self.districts:
            if on_screen_rect(d.rect, cam, screen_w, screen_h):
                x, y, w, h = d.rect
                pygame.draw.rect(surf, d.ground, (x - cam[0], y - cam[1], w, h))
        pygame.draw.rect(surf, WATER, (int(0 - cam[0]), int(6550 - cam[1]), MAP_W, 650))

    def draw_roads(self, surf, cam, screen_w, screen_h):
        for road in self.sidewalks:
            if on_screen_rect(road, cam, screen_w, screen_h):
                x, y, w, h = road
                pygame.draw.rect(surf, SIDEWALK, (int(x - cam[0]), int(y - cam[1]), w, h))
        for road in self.roads:
            if not on_screen_rect(road, cam, screen_w, screen_h):
                continue
            x, y, w, h = road
            sx, sy = int(x - cam[0]), int(y - cam[1])
            pygame.draw.rect(surf, ROAD, (sx, sy, w, h))
            if w > h:
                for lx in range(sx, sx + w, 92):
                    pygame.draw.rect(surf, ROAD_LINE, (lx, sy + h // 2 - 2, 46, 4))
            else:
                for ly in range(sy, sy + h, 92):
                    pygame.draw.rect(surf, ROAD_LINE, (sx + w // 2 - 2, ly, 4, 46))

    def draw_buildings(self, surf, cam, screen_w, screen_h):
        for b in self.buildings:
            if on_screen_rect(b.rect, cam, screen_w, screen_h):
                draw_building(surf, b, cam)

    def draw_decorations(self, surf, cam, screen_w, screen_h, night_alpha=0):
        for kind, x, y in self.decorations:
            if not on_screen_rect((x - 30, y - 30, 60, 60), cam, screen_w, screen_h):
                continue
            sx, sy = int(x - cam[0]), int(y - cam[1])
            if kind == "tree":
                draw_tree(surf, sx, sy)
            elif kind == "light":
                draw_streetlight(surf, sx, sy, night_alpha)
            elif kind == "smoke":
                pygame.draw.circle(surf, (120, 120, 120, 90), (sx, sy), 15)
                pygame.draw.circle(surf, (150, 150, 150, 70), (sx + 12, sy - 18), 20)
            else:
                pygame.draw.rect(surf, (80, 55, 40), (sx - 12, sy - 4, 24, 8))
