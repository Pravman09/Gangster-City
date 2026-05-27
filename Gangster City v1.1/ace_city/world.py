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
    def __init__(self, city_id=1):
        self.city_id = city_id
        self.name = "Gangster City" if city_id == 1 else "City 2"
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
        if self.city_id == 2:
            return [
                District("Airport Strip", (500, 700, 2300, 1500), (54, 58, 64),
                         ["hotel", "garage", "gas", "store"], [(120, 125, 135), (95, 105, 115), (150, 145, 120)], "runways and terminals"),
                District("Neon Blocks", (3100, 650, 2400, 1800), (38, 42, 58),
                         ["store", "restaurant", "gunshop", "apartment"], [(150, 70, 135), (60, 125, 165), (190, 110, 70)], "clubs and neon"),
                District("Financial Core", (5800, 850, 2500, 1800), (34, 48, 56),
                         ["office", "bank", "apartment"], [(75, 105, 130), (95, 125, 145), (145, 130, 95)], "money towers"),
                District("Old Harbor", (650, 3600, 2500, 2100), (54, 62, 66),
                         ["warehouse", "factory", "garage"], [(85, 95, 100), (105, 95, 80), (70, 85, 95)], "docks and containers"),
                District("Cartel Row", (3550, 3700, 2400, 2100), (64, 50, 48),
                         ["slum", "gunshop", "store", "warehouse"], [(135, 70, 60), (105, 58, 62), (155, 100, 72)], "gang blocks"),
                District("Hill Estates", (6400, 3900, 2300, 1900), (38, 96, 62),
                         ["villa", "bank", "hospital"], [(230, 215, 178), (190, 175, 145), (165, 185, 150)], "guarded estates"),
                District("Military Yard", (3900, 2500, 2200, 900), (66, 70, 62),
                         ["factory", "warehouse", "police"], [(95, 105, 88), (120, 120, 100), (75, 95, 110)], "restricted roads"),
            ]
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
        if self.city_id == 2:
            special = [
                ((1080, 1150, 560, 260), "airport", (125, 128, 135), "Airport Strip", "CITY 2 AIRPORT"),
                ((1780, 1320, 230, 155), "garage", (95, 90, 85), "Airport Strip", "TUNER"),
                ((2320, 1180, 210, 150), "gas", (190, 55, 45), "Airport Strip", "FUEL"),
                ((3820, 1500, 220, 150), "gunshop", (88, 74, 82), "Neon Blocks", "ELITE GUNS"),
                ((4320, 1320, 220, 150), "hospital", (222, 222, 216), "Neon Blocks", "TRAUMA"),
                ((6980, 1560, 310, 220), "bank", (145, 128, 86), "Financial Core", "CORE BANK"),
                ((7600, 1260, 250, 170), "police", (70, 110, 175), "Financial Core", "SWAT HQ"),
                ((1650, 4550, 330, 210), "bank", (120, 112, 88), "Old Harbor", "HARBOR VAULT"),
                ((2350, 5000, 280, 180), "garage", (95, 90, 85), "Old Harbor", "DOCK GARAGE"),
                ((4750, 4700, 230, 155), "gunshop", (90, 62, 62), "Cartel Row", "BLACK MARKET"),
                ((5050, 5050, 300, 210), "bank", (135, 112, 82), "Cartel Row", "CARTEL CASH"),
                ((7050, 4480, 260, 190), "villa", (220, 205, 170), "Hill Estates", "BOSS ESTATE"),
                ((7550, 5050, 280, 180), "hospital", (222, 222, 216), "Hill Estates", "PRIVATE CLINIC"),
                ((4700, 2850, 420, 260), "factory", (92, 98, 88), "Military Yard", "ARMORY"),
                ((5350, 2820, 260, 180), "police", (70, 110, 175), "Military Yard", "TACTICAL UNIT"),
            ]
        else:
            special = [
                ((900, 6200, 560, 260), "airport", (125, 128, 135), "Outskirts", "AIRPORT"),
                ((4080, 5000, 260, 180), "police", (70, 110, 175), "Civic Center", "POLICE HQ"),
            ((4550, 5050, 250, 170), "hospital", (222, 222, 216), "Civic Center", "HOSPITAL"),
            ((4200, 2700, 300, 220), "bank", (125, 112, 82), "Downtown", "BANK"),
            ((1850, 1200, 190, 135), "gunshop", (74, 72, 82), "Market Mile", "GUNS"),
            ((8350, 1450, 230, 155), "police", (70, 110, 175), "Rich Hills", "POLICE"),
            ((7700, 1750, 230, 155), "hospital", (222, 222, 216), "Rich Hills", "CLINIC"),
            ((6900, 900, 230, 170), "bank", (135, 122, 84), "Rich Hills", "BANK"),
            ((1280, 5050, 220, 150), "police", (70, 110, 175), "Slums", "PRECINCT"),
            ((2050, 5480, 220, 150), "hospital", (222, 222, 216), "Slums", "CLINIC"),
            ((1760, 4580, 210, 145), "gunshop", (76, 67, 64), "Slums", "GUNS"),
            ((7120, 5850, 230, 155), "police", (70, 110, 175), "Industrial", "POLICE"),
            ((8000, 4850, 230, 155), "hospital", (222, 222, 216), "Industrial", "MEDICAL"),
            ((7750, 5300, 220, 150), "bank", (125, 112, 82), "Industrial", "BANK"),
            ((2550, 1380, 220, 150), "bank", (135, 122, 84), "Market Mile", "BANK"),
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
        target_buildings = 680 if self.city_id == 2 else 580
        while len(self.buildings) < target_buildings and attempts < 30000:
            attempts += 1
            d = random.choice(self.districts)
            dx, dy, dw, dh = d.rect
            if d.name == "Green Park" and random.random() < 0.85:
                continue
            w = random.randint(80, 210)
            h = random.randint(70, 190)
            if d.name == "Downtown":
                w, h = random.randint(110, 260), random.randint(160, 340)
            if d.name in ("Industrial", "Old Harbor", "Military Yard"):
                w, h = random.randint(180, 360), random.randint(120, 280)
            if d.name == "Financial Core":
                w, h = random.randint(120, 280), random.randint(180, 360)
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
            if d.name in ("Green Park", "Rich Hills", "Hill Estates"):
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
        water_y = 6550 if self.city_id == 1 else 6100
        pygame.draw.rect(surf, WATER, (int(0 - cam[0]), int(water_y - cam[1]), MAP_W, MAP_H - water_y))

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


