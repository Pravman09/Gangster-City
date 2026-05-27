import json
import math
from pathlib import Path
import random
import pygame
from .config import BLACK, BLUE, FPS, GREEN, MAP_H, MAP_W, RED, SCREEN_H, SCREEN_W, WHITE, YELLOW
from .entities import Bullet, Civilian, Enemy, Grenade, Player, Police, Vehicle
from .missions import MissionSystem
from .particles import DamageNumber, Particle
from .systems import AudioSystem, EnvironmentSystem, WantedSystem
from .utils import clamp, dist, on_screen_rect
from .world import City


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Gangster City")
        self.fullscreen = False
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 28)
        self.font_small = pygame.font.Font(None, 19)
        self.current_city = 1
        self.city_mission_indices = {1: 0, 2: 0}
        self.city_positions = {1: [1280, 1450], 2: [1280, 1150]}
        self.city = City(self.current_city)
        self.environment = EnvironmentSystem()
        self.wanted = WantedSystem()
        self.audio = AudioSystem()
        self.missions = MissionSystem()
        self.state = "menu"
        self.running = True
        self.start_button = pygame.Rect(SCREEN_W // 2 - 140, SCREEN_H // 2 - 35, 280, 48)
        self.mission_log_button = pygame.Rect(SCREEN_W // 2 - 140, SCREEN_H // 2 + 25, 280, 48)
        self.save_quit_button = pygame.Rect(SCREEN_W // 2 - 140, SCREEN_H // 2 + 85, 280, 48)
        self.clear_button = pygame.Rect(SCREEN_W // 2 - 140, SCREEN_H // 2 + 145, 280, 48)
        self.quit_button = pygame.Rect(SCREEN_W // 2 - 140, SCREEN_H // 2 + 205, 280, 48)
        self.save_path = Path(__file__).resolve().parent.parent / "gangster_city_save.json"
        self.legacy_save_path = Path(__file__).resolve().parent.parent / "ace_gangster_save.json"
        self.reset_world()
        self.load_game()

    def reset_world(self):
        self.cam = [0, 0]
        self.player = Player(*self.city_positions.get(self.current_city, [1280, 1450]))
        car_colors = [(150, 35, 35), (40, 80, 150), (210, 190, 80), (35, 120, 90), (180, 180, 185), (35, 35, 40)]
        city2_models = ["supercar", "street_racer", "armored_suv", "luxury", "black_van"]
        car_count = 75 if self.current_city == 2 else 55
        traffic_count = 95 if self.current_city == 2 else 75
        self.cars = [Vehicle(*self.city.random_open_position(120, 25), color=random.choice(car_colors), model=random.choice(city2_models) if self.current_city == 2 else None) for _ in range(car_count)]
        self.traffic = [Vehicle(*self.city.random_open_position(120, 25), color=random.choice(car_colors), traffic=True, model=random.choice(city2_models) if self.current_city == 2 and random.random() < 0.55 else None) for _ in range(traffic_count)]
        police_district = "Financial Core" if self.current_city == 2 else "Civic Center"
        self.traffic.extend(Vehicle(*self.city.random_open_position(120, 25, police_district), traffic=True, model="tuned_police" if self.current_city == 2 else "police") for _ in range(18 if self.current_city == 2 else 12))
        enemy_districts = ["Neon Blocks", "Old Harbor", "Cartel Row", "Military Yard"] if self.current_city == 2 else ["Slums", "Industrial", "Market Mile"]
        police_districts = ["Financial Core", "Airport Strip", "Military Yard"] if self.current_city == 2 else ["Civic Center", "Downtown", "Market Mile"]
        self.enemies = [Enemy(*self.city.random_open_position(120, 18, random.choice(enemy_districts)), elite=self.current_city == 2) for _ in range(48 if self.current_city == 2 else 30)]
        self.police = [Police(*self.city.random_open_position(120, 18, random.choice(police_districts))) for _ in range(52 if self.current_city == 2 else 34)]
        self.police.extend(Police(*self.city.random_open_position(120, 18, police_districts[0])) for _ in range(12 if self.current_city == 2 else 8))
        self.civilians = [Civilian(*self.city.random_open_position(120, 18)) for _ in range(105 if self.current_city == 2 else 85)]
        self.bullets = []
        self.particles = []
        self.damage_numbers = []
        self.mission_enemies = []
        self.spawn_timer = 15.0
        self.toast = "Story mode: start as nobody. Find the first mission marker."
        self.toast_timer = 5
        self.kills = 0
        self.civilians_hit = 0
        self.missions = MissionSystem(self.current_city)
        self.missions.index = self.city_mission_indices.get(self.current_city, 0)
        self.wanted = WantedSystem()
        self.game_over = False
        self.last_bank_robbed = False
        self.bank_heist_timer = 0
        self.gunshop_selection = 0
        self.gunshop_items = self.default_gunshop_items()
        self.current_building = None
        self.interior_selection = 0
        self.autosave_timer = 10.0

    def spawn_mission_enemies(self, center, count):
        self.mission_enemies = []
        for _ in range(count):
            x = center[0] + random.randint(-180, 180)
            y = center[1] + random.randint(-180, 180)
            e = Enemy(x, y)
            e.role = random.choice(["flank", "guard"])
            self.enemies.append(e)
            self.mission_enemies.append(e)

    def spawn_actor(self):
        if self.current_city == 2:
            if random.random() < 0.62:
                self.enemies.append(Enemy(*self.city.random_open_position(120, 18, random.choice(["Neon Blocks", "Old Harbor", "Cartel Row"])), elite=True))
            elif random.random() < 0.82:
                self.police.append(Police(*self.city.random_open_position(120, 18, "Financial Core")))
            else:
                self.civilians.append(Civilian(*self.city.random_open_position(120, 18)))
            return
        if random.random() < 0.55:
            self.enemies.append(Enemy(*self.city.random_open_position(120, 18, random.choice(["Slums", "Industrial"]))))
        elif random.random() < 0.72:
            self.police.append(Police(*self.city.random_open_position(120, 18, "Civic Center")))
        else:
            self.civilians.append(Civilian(*self.city.random_open_position(120, 18)))

    def city_name(self):
        return "Gangster City" if self.current_city == 1 else "City 2"

    def default_gunshop_items(self):
        if self.current_city == 2:
            return [
                ("SMG", 900),
                ("Heavy Rifle", 1400),
                ("Combat Shotgun", 1600),
                ("Heavy Armor", 850),
                ("Tactical Armor", 1800),
                ("Rocket Launcher", 3000),
                ("Grenades x5", 600),
            ]
        return [
            ("Pistol", 120),
            ("Shotgun", 260),
            ("Rifle", 420),
            ("Armor", 160),
            ("Grenades x3", 180),
        ]

    def switch_city(self, city_id):
        if city_id == self.current_city:
            return
        self.city_positions[self.current_city] = self.player.pos[:]
        self.city_mission_indices[self.current_city] = self.missions.index
        weapons = list(self.player.weapons.keys())
        player_data = {
            "health": self.player.health,
            "armor": self.player.armor,
            "money": self.player.money,
            "weapon": self.player.weapon,
            "weapons": weapons,
            "grenades": self.player.grenades,
            "reputation": self.player.reputation,
        }
        self.current_city = city_id
        self.city = City(self.current_city)
        self.reset_world()
        self.player.health = player_data["health"]
        self.player.armor = player_data["armor"]
        self.player.money = player_data["money"]
        self.player.weapons = {"None": None}
        for weapon in player_data["weapons"]:
            if weapon != "None":
                self.player.unlock_weapon(weapon)
        self.player.weapon = player_data["weapon"] if player_data["weapon"] in self.player.weapons or player_data["weapon"] == "None" else "None"
        self.player.grenades = player_data["grenades"]
        self.player.reputation = player_data["reputation"]
        airport = next((b for b in self.city.landmarks if b.kind == "airport"), None)
        if airport:
            self.player.pos = [airport.rect[0] + airport.rect[2] / 2, airport.rect[1] + airport.rect[3] + 80]
        self.city_mission_indices[self.current_city] = self.missions.index
        self.cam = [self.player.pos[0] - SCREEN_W // 2, self.player.pos[1] - SCREEN_H // 2]
        self.toast = f"Arrived in {self.city_name()}"
        self.toast_timer = 5
        self.save_game()

    def events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                if self.state != "menu":
                    self.save_game()
                self.running = False
            if self.state == "menu":
                self.menu_events(e)
                continue
            if self.state == "gunshop":
                self.gunshop_events(e)
                continue
            if self.state == "interior":
                self.interior_events(e)
                continue
            if self.state == "map":
                self.map_events(e)
                continue
            if self.state == "mission_log":
                self.mission_log_events(e)
                continue
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_f:
                    self.toggle_fullscreen()
                    continue
                if self.game_over and e.key == pygame.K_r:
                    self.reset_world()
                if e.key == pygame.K_ESCAPE:
                    self.save_game()
                    self.state = "menu"
                if e.key == pygame.K_m and not self.game_over:
                    self.state = "map"
                if pygame.K_1 <= e.key <= pygame.K_9:
                    self.player.switch_weapon(e.key - pygame.K_1)
                if e.key == pygame.K_e and not self.game_over:
                    self.interact()
                if e.key == pygame.K_z and not self.game_over:
                    self.enter_nearest_building()
                if e.key == pygame.K_h:
                    self.try_service("hospital")
                if e.key == pygame.K_g:
                    self.try_service("garage")
                if e.key == pygame.K_b:
                    self.try_service("bank")
            if e.type == pygame.MOUSEBUTTONDOWN and not self.game_over:
                mx, my = e.pos
                if self.player.shoot(mx + self.cam[0], my + self.cam[1], self.bullets):
                    self.audio.play("gun")

    def menu_events(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_f:
                self.toggle_fullscreen()
                return
            if e.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.load_game()
                self.state = "playing"
            elif e.key == pygame.K_m:
                self.state = "mission_log"
            elif e.key == pygame.K_s:
                self.save_game()
                self.running = False
            elif e.key == pygame.K_c:
                self.clear_database()
            elif e.key in (pygame.K_q, pygame.K_ESCAPE):
                self.running = False
        if e.type == pygame.MOUSEBUTTONDOWN:
            if self.start_button.collidepoint(e.pos):
                self.load_game()
                self.state = "playing"
            elif self.mission_log_button.collidepoint(e.pos):
                self.state = "mission_log"
            elif self.save_quit_button.collidepoint(e.pos):
                self.save_game()
                self.running = False
            elif self.clear_button.collidepoint(e.pos):
                self.clear_database()
            elif self.quit_button.collidepoint(e.pos):
                self.running = False

    def save_game(self):
        self.city_mission_indices[self.current_city] = self.missions.index
        self.city_positions[self.current_city] = self.player.pos[:]
        data = {
            "player": {
                "pos": self.player.pos,
                "health": self.player.health,
                "armor": self.player.armor,
                "money": self.player.money,
                "weapons": list(self.player.weapons.keys()),
                "weapon": self.player.weapon,
                "grenades": self.player.grenades,
                "reputation": self.player.reputation,
            },
            "current_city": self.current_city,
            "city_mission_indices": {str(k): v for k, v in self.city_mission_indices.items()},
            "city_positions": {str(k): v for k, v in self.city_positions.items()},
            "mission_index": self.missions.index,
            "kills": self.kills,
            "civilians_hit": self.civilians_hit,
            "environment": {"time": self.environment.time, "weather": self.environment.weather},
        }
        self.save_path.write_text(json.dumps(data, indent=2))

    def load_game(self):
        if not self.save_path.exists() and self.legacy_save_path.exists():
            self.save_path.write_text(self.legacy_save_path.read_text())
        if not self.save_path.exists():
            return
        try:
            data = json.loads(self.save_path.read_text())
        except (OSError, json.JSONDecodeError):
            return
        self.current_city = data.get("current_city", 1)
        self.city_mission_indices = {int(k): v for k, v in data.get("city_mission_indices", {"1": data.get("mission_index", 0), "2": 0}).items()}
        self.city_positions = {int(k): v for k, v in data.get("city_positions", {"1": [1280, 1450], "2": [1280, 1150]}).items()}
        self.city = City(self.current_city)
        self.reset_world()
        p = data.get("player", {})
        self.player.pos = list(p.get("pos", self.player.pos))
        self.player.health = p.get("health", self.player.max_health)
        self.player.armor = p.get("armor", 0)
        self.player.money = p.get("money", self.player.money)
        self.player.weapons = {"None": None}
        for weapon in p.get("weapons", ["None"]):
            if weapon != "None":
                self.player.unlock_weapon(weapon)
        self.player.weapon = p.get("weapon", "None")
        if self.player.weapon != "None" and self.player.weapon not in self.player.weapons:
            self.player.weapon = "None"
        self.player.grenades = p.get("grenades", 0)
        self.player.reputation = p.get("reputation", 0)
        self.missions.index = min(self.city_mission_indices.get(self.current_city, data.get("mission_index", 0)), len(self.missions.missions))
        self.kills = data.get("kills", 0)
        self.civilians_hit = data.get("civilians_hit", 0)
        env = data.get("environment", {})
        self.environment.time = env.get("time", self.environment.time)
        self.environment.weather = env.get("weather", self.environment.weather)
        self.city_mission_indices[self.current_city] = self.missions.index
        self.cam = [self.player.pos[0] - SCREEN_W // 2, self.player.pos[1] - SCREEN_H // 2]
        self.toast = "Save loaded"
        self.toast_timer = 3

    def clear_database(self):
        if self.save_path.exists():
            self.save_path.unlink()
        self.current_city = 1
        self.city_mission_indices = {1: 0, 2: 0}
        self.city_positions = {1: [1280, 1450], 2: [1280, 1150]}
        self.city = City(self.current_city)
        self.reset_world()
        self.toast = "Database cleared"
        self.toast_timer = 4

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        flags = pygame.FULLSCREEN if self.fullscreen else 0
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), flags)

    def map_events(self, e):
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_m, pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
            self.state = "playing"

    def mission_log_events(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_ESCAPE, pygame.K_m, pygame.K_RETURN, pygame.K_SPACE):
                self.state = "menu"
        if e.type == pygame.MOUSEBUTTONDOWN:
            self.state = "menu"

    def gunshop_events(self, e):
        if e.type != pygame.KEYDOWN:
            return
        if e.key in (pygame.K_ESCAPE, pygame.K_e):
            self.state = "playing"
        elif e.key in (pygame.K_w, pygame.K_UP):
            self.gunshop_selection = (self.gunshop_selection - 1) % len(self.gunshop_items)
        elif e.key in (pygame.K_s, pygame.K_DOWN):
            self.gunshop_selection = (self.gunshop_selection + 1) % len(self.gunshop_items)
        elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.buy_gunshop_item()
        elif pygame.K_1 <= e.key <= pygame.K_9:
            self.gunshop_selection = e.key - pygame.K_1
            if self.gunshop_selection < len(self.gunshop_items):
                self.buy_gunshop_item()

    def buy_gunshop_item(self):
        item, price = self.gunshop_items[self.gunshop_selection]
        if self.player.money < price:
            self.toast = "Gun shop: not enough money"
            self.toast_timer = 3
            return
        self.player.money -= price
        if item == "Armor":
            self.player.armor = 50
        elif item == "Heavy Armor":
            self.player.armor = 100
        elif item == "Tactical Armor":
            self.player.armor = 150
        elif item.startswith("Grenades"):
            self.player.unlock_weapon("Grenade")
            self.player.grenades += 5 if "x5" in item else 3
        else:
            self.player.unlock_weapon(item)
        self.toast = f"Gun shop: bought {item}"
        self.toast_timer = 3
        self.save_game()

    def interior_events(self, e):
        if e.type != pygame.KEYDOWN:
            return
        items = self.interior_items()
        if e.key in (pygame.K_ESCAPE, pygame.K_z):
            self.state = "playing"
            self.current_building = None
        elif e.key in (pygame.K_w, pygame.K_UP) and items:
            self.interior_selection = (self.interior_selection - 1) % len(items)
        elif e.key in (pygame.K_s, pygame.K_DOWN) and items:
            self.interior_selection = (self.interior_selection + 1) % len(items)
        elif e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e) and items:
            self.buy_interior_item()
        elif pygame.K_1 <= e.key <= pygame.K_9 and items:
            idx = e.key - pygame.K_1
            if idx < len(items):
                self.interior_selection = idx
                self.buy_interior_item()

    def interact(self):
        if self.player.in_car:
            self.player.in_car.driver = None
            self.player.in_car = None
            return
        for car in self.cars + self.traffic:
            if not car.driver and dist(car.pos, self.player.pos) < 58:
                self.player.in_car = car
                car.driver = self.player
                return
        if self.nearest_service("gunshop", 190):
            self.state = "gunshop"
            return
        self.try_service("store")

    def nearest_building(self, radius=175):
        matches = [b for b in self.city.buildings
                   if dist((b.rect[0] + b.rect[2] / 2, b.rect[1] + b.rect[3] / 2), self.player.pos) < radius]
        return min(matches, key=lambda b: dist((b.rect[0] + b.rect[2] / 2, b.rect[1] + b.rect[3] / 2), self.player.pos)) if matches else None

    def enter_nearest_building(self):
        building = self.nearest_building()
        if not building:
            self.toast = "No building entrance nearby"
            self.toast_timer = 2
            return
        self.current_building = building
        self.interior_selection = 0
        self.state = "interior"

    def nearest_service(self, kind, radius=180):
        matches = [b for b in self.city.landmarks + self.city.buildings
                   if b.kind == kind and dist((b.rect[0] + b.rect[2] / 2, b.rect[1] + b.rect[3] / 2), self.player.pos) < radius]
        return matches[0] if matches else None

    def try_service(self, kind):
        if not self.nearest_service(kind):
            return
        if kind == "hospital" and self.player.money >= 50:
            self.player.money -= 50
            self.player.health = self.player.max_health
            self.toast = "Hospital: healed for $50"
        elif kind == "garage" and self.player.money >= 75:
            self.player.money -= 75
            self.player.armor = 50
            self.toast = "Garage: armor installed for $75"
        elif kind == "bank":
            self.player.money += 25
            self.toast = "Bank: collected a small account payout"
        elif kind == "store" and self.player.money >= 120:
            self.player.money -= 120
            self.player.unlock_weapon("Pistol")
            self.toast = "Store: bought a pistol"
        self.toast_timer = 4
        self.save_game()

    def interior_items(self):
        if not self.current_building:
            return []
        kind = self.current_building.kind
        if kind in ("store", "restaurant", "gas"):
            if self.current_city == 2:
                return [("Snack Heal +30 HP", 45), ("Med Pack Full Heal", 160), ("Heavy Armor", 700), ("Grenades x5", 520)]
            return [("Snack Heal +20 HP", 25), ("Medkit Full Heal", 80), ("Light Armor", 120), ("Grenade", 75)]
        if kind == "hospital":
            return [("Heal +40 HP", 45), ("Full Heal", 90), ("Armor Patch", 90)]
        if kind == "gunshop":
            return self.gunshop_items
        if kind == "garage":
            if self.current_city == 2:
                return [("Full Repair", 250), ("Engine Upgrade", 900), ("Turbo Tune", 1400), ("Armor Plating", 1200), ("Spawn Supercar", 2200)]
            return [("Repair Current Car", 80), ("Armor", 130), ("Performance Tune", 220)]
        if kind == "bank":
            return [("Withdraw $100", 0), ("Rob Bank", 0)]
        if kind == "airport":
            if self.current_city == 1:
                return [("Fly to City 2", 1000)]
            return [("Fly to Gangster City", 500)]
        return []

    def trigger_bank_robbery(self):
        bank = self.current_building
        if not bank:
            return
        payout = random.randint(1800, 3200) if self.current_city == 2 else random.randint(650, 1050)
        self.player.money += payout
        self.last_bank_robbed = True
        self.bank_heist_timer = 65 if self.current_city == 2 else 45
        self.wanted.level = max(self.wanted.level, 5 if self.current_city == 2 else 4)
        self.wanted.timer = max(self.wanted.timer, 65.0 if self.current_city == 2 else 45.0)
        self.wanted.reason = "bank robbery alarm"

        cx = bank.rect[0] + bank.rect[2] / 2
        cy = bank.rect[1] + bank.rect[3] / 2
        self.player.pos = [cx, bank.rect[1] + bank.rect[3] + 70]
        if self.player.in_car:
            self.player.in_car.driver = None
            self.player.in_car = None

        for _ in range(16 if self.current_city == 2 else 10):
            angle = random.random() * math.tau
            radius = random.randint(170, 360)
            cop = Police(cx + math.cos(angle) * radius, cy + math.sin(angle) * radius)
            cop.shoot_timer = random.uniform(0.2, 0.7)
            self.police.append(cop)

        for _ in range(8 if self.current_city == 2 else 5):
            angle = random.random() * math.tau
            radius = random.randint(260, 520)
            car = Vehicle(cx + math.cos(angle) * radius, cy + math.sin(angle) * radius, traffic=True, model="tuned_police" if self.current_city == 2 else "police")
            car.speed = random.randint(90, 150)
            self.traffic.append(car)

        self.current_building = None
        self.state = "playing"
        self.player.noise_timer = 8
        self.toast = f"BANK ALARM! Stole ${payout}. Survive the police response!"
        self.toast_timer = 6
        self.save_game()
    def buy_interior_item(self):
        items = self.interior_items()
        if not items:
            return
        item, price = items[self.interior_selection]
        if self.player.money < price:
            self.toast = "Not enough money"
            self.toast_timer = 3
            return
        self.player.money -= price
        if item.startswith("Snack"):
            self.player.health = min(self.player.max_health, self.player.health + 20)
        elif item.startswith("Heal +40"):
            self.player.health = min(self.player.max_health, self.player.health + 40)
        elif item.startswith("Snack Heal +30"):
            self.player.health = min(self.player.max_health, self.player.health + 30)
        elif item.startswith("Medkit") or item.startswith("Med Pack") or item.startswith("Full Heal"):
            self.player.health = self.player.max_health
        elif item in ("Light Armor", "Armor", "Armor Patch"):
            self.player.armor = 50
        elif item == "Heavy Armor":
            self.player.armor = 100
        elif item == "Tactical Armor":
            self.player.armor = 150
        elif item.startswith("Grenades"):
            self.player.unlock_weapon("Grenade")
            self.player.grenades += 5 if "x5" in item else 3
        elif item == "Grenade":
            self.player.unlock_weapon("Grenade")
            self.player.grenades += 1
        elif item in ("Pistol", "Shotgun", "Rifle", "SMG", "Heavy Rifle", "Combat Shotgun", "Rocket Launcher"):
            self.player.unlock_weapon(item)
        elif item in ("Repair Current Car", "Full Repair") and self.player.in_car:
            self.player.in_car.health = 180
        elif item in ("Performance Tune", "Engine Upgrade", "Turbo Tune") and self.player.in_car:
            self.player.in_car.max_speed += 160 if self.current_city == 2 else 80
            self.player.in_car.accel += 140 if self.current_city == 2 else 70
        elif item == "Armor Plating" and self.player.in_car:
            self.player.in_car.health += 220
        elif item == "Spawn Supercar":
            self.cars.append(Vehicle(self.player.pos[0] + 70, self.player.pos[1], color=(190, 35, 50), model="supercar"))
        elif item.startswith("Withdraw"):
            self.player.money += 100
        elif item == "Rob Bank":
            self.trigger_bank_robbery()
            return
        elif item == "Fly to City 2":
            self.switch_city(2)
            return
        elif item == "Fly to Gangster City":
            self.switch_city(1)
            return
        self.toast = f"{self.current_building.label}: {item}"
        self.toast_timer = 3
        self.save_game()

    def update(self, dt):
        if self.state in ("menu", "gunshop"):
            return
        if self.state == "interior":
            self.missions.update(dt, self)
            return
        if self.state in ("map", "mission_log"):
            return
        self.environment.update(dt)
        self.wanted.update(dt)
        if self.bank_heist_timer > 0:
            self.bank_heist_timer -= dt
            self.wanted.level = max(self.wanted.level, 3)
            self.wanted.timer = max(self.wanted.timer, 3.0)
            if self.bank_heist_timer <= 0:
                self.toast = "Bank heat cooling down. Find somewhere quiet."
                self.toast_timer = 4
        if self.toast_timer > 0:
            self.toast_timer -= dt
        if self.game_over:
            return
        self.player.update(dt, self.city)
        combat_alert = self.player.noise_timer > 0 or self.wanted.level > 0
        for car in self.cars + self.traffic:
            if on_screen_rect((car.pos[0] - 500, car.pos[1] - 500, 1000, 1000), self.cam, SCREEN_W, SCREEN_H, 1000) or car.driver:
                car.update(dt, self.city)
        for enemy in self.enemies:
            if self.near_active(enemy.pos):
                enemy.update(dt, self.player, self.city, self.bullets, combat_alert)
        for cop in self.police:
            if self.near_active(cop.pos):
                cop.update(dt, self.player, self.city, self.bullets, self.wanted.level, self.enemies)
        for civ in self.civilians:
            if self.near_active(civ.pos):
                civ.update(dt, self.player, self.city, combat_alert)
        self.update_bullets(dt)
        self.check_vehicle_hits()
        self.missions.update(dt, self)
        self.autosave_timer -= dt
        if self.autosave_timer <= 0:
            self.save_game()
            self.autosave_timer = 10.0
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_actor()
            self.spawn_timer = 15.0
        self.particles = [p for p in self.particles if p.update(dt)]
        self.damage_numbers = [d for d in self.damage_numbers if d.update(dt)]
        self.cam[0] += (self.player.pos[0] - SCREEN_W // 2 - self.cam[0]) * 0.1
        self.cam[1] += (self.player.pos[1] - SCREEN_H // 2 - self.cam[1]) * 0.1
        self.cam[0] = clamp(self.cam[0], 0, MAP_W - SCREEN_W)
        self.cam[1] = clamp(self.cam[1], 0, MAP_H - SCREEN_H)
        if self.player.health <= 0:
            self.handle_player_death()

    def handle_player_death(self):
        penalty = min(500, self.player.money)
        self.player.money -= penalty
        self.player.health = self.player.max_health
        self.player.armor = 0
        if self.player.in_car:
            self.player.in_car.driver = None
            self.player.in_car = None
        self.player.pos = [4550, 5050]
        self.bullets = []
        self.particles = []
        self.damage_numbers = []
        self.wanted = WantedSystem()
        self.toast = f"Hospital bill: -${penalty}. Weapons kept."
        self.toast_timer = 5
        self.save_game()

    def near_active(self, pos):
        return abs(pos[0] - self.player.pos[0]) < 1300 and abs(pos[1] - self.player.pos[1]) < 1000

    def update_bullets(self, dt):
        live = []
        remove = set()
        for b in self.bullets:
            if isinstance(b, Grenade):
                if b.update(dt):
                    live.append(b)
                else:
                    self.explode_grenade(b, remove)
            elif b.update(dt):
                live.append(b)
        self.bullets = live
        for b in self.bullets:
            if isinstance(b, Grenade):
                continue
            if b.owner == "player":
                self.hit_group(b, self.enemies, remove, RED, reward=12)
                self.hit_group(b, self.police, remove, BLUE, crime="attacked police")
                self.hit_group(b, self.civilians, remove, RED, crime="hurt civilian", civilian=True)
            elif b.owner in ("enemy", "police"):
                if b.owner == "enemy":
                    self.hit_group(b, self.police, remove, BLUE)
                if b.owner == "police":
                    self.hit_group(b, self.enemies, remove, RED, reward=0)
                if dist(b.pos, self.player.pos) < 17:
                    self.player.take_damage(b.damage)
                    self.damage_numbers.append(DamageNumber(self.player.pos, b.damage, RED))
                    remove.add(b)
        self.bullets = [b for b in self.bullets if b not in remove]

    def explode_grenade(self, grenade, remove):
        remove.add(grenade)
        self.player.noise_timer = 5
        for group, color, crime, civilian in ((self.enemies, RED, None, False), (self.police, BLUE, "explosion near police", False), (self.civilians, RED, "explosion near civilians", True)):
            for actor in group:
                if actor.alive and dist(actor.pos, grenade.pos) < grenade.radius:
                    actor.take_damage(grenade.damage)
                    self.damage_numbers.append(DamageNumber(actor.pos, grenade.damage, color))
                    if not actor.alive:
                        if civilian:
                            self.civilians_hit += 1
                        else:
                            self.kills += 1
                        if crime:
                            self.wanted.crime(crime)
        if dist(self.player.pos, grenade.pos) < grenade.radius:
            self.player.take_damage(35)
        for _ in range(32):
            a = random.random() * math.tau
            speed = random.randint(180, 420)
            self.particles.append(Particle(grenade.pos, (math.cos(a) * speed, math.sin(a) * speed), random.choice([RED, YELLOW, (255, 130, 40)]), 0.65, random.randint(3, 6)))

    def hit_group(self, bullet, group, remove, color, reward=0, crime=None, civilian=False):
        if bullet in remove:
            return
        for actor in group:
            if actor.alive and dist(actor.pos, bullet.pos) < 17:
                actor.take_damage(bullet.damage)
                self.damage_numbers.append(DamageNumber(actor.pos, bullet.damage, color))
                if not actor.alive:
                    self.kills += 0 if civilian else 1
                    self.player.money = max(0, self.player.money + reward - (50 if civilian else 0))
                    if civilian:
                        self.civilians_hit += 1
                    if crime:
                        self.wanted.crime(crime)
                    for _ in range(16 if self.current_city == 2 else 10):
                        a = random.random() * math.tau
                        self.particles.append(Particle(actor.pos, (math.cos(a) * 240, math.sin(a) * 240), color, 0.45, 3))
                remove.add(bullet)
                return

    def check_vehicle_hits(self):
        car = self.player.in_car
        if not car or abs(car.speed) < 260:
            return
        for group, color, crime, reward in ((self.enemies, RED, None, 10), (self.police, BLUE, "ran over police", 0), (self.civilians, RED, "ran over civilian", -50)):
            for actor in group:
                if actor.alive and dist(actor.pos, car.pos) < 34:
                    actor.alive = False
                    self.damage_numbers.append(DamageNumber(actor.pos, "HIT", color))
                    self.player.money = max(0, self.player.money + reward)
                    if crime:
                        self.wanted.crime(crime)
                    if group is self.civilians:
                        self.civilians_hit += 1
                    else:
                        self.kills += 1

    def draw(self):
        if self.state == "menu":
            self.draw_menu()
            pygame.display.flip()
            return
        if self.state == "gunshop":
            self.draw_gunshop()
            pygame.display.flip()
            return
        if self.state == "interior":
            self.draw_interior()
            pygame.display.flip()
            return
        if self.state == "map":
            self.draw_full_map()
            pygame.display.flip()
            return
        if self.state == "mission_log":
            self.draw_mission_log()
            pygame.display.flip()
            return
        self.city.draw_ground(self.screen, self.cam, SCREEN_W, SCREEN_H)
        self.city.draw_roads(self.screen, self.cam, SCREEN_W, SCREEN_H)
        self.city.draw_decorations(self.screen, self.cam, SCREEN_W, SCREEN_H, 60 if self.environment.night_alpha else 0)
        self.city.draw_buildings(self.screen, self.cam, SCREEN_W, SCREEN_H)
        self.missions.draw_marker(self.screen, self.cam, self.font_small)
        for car in self.cars + self.traffic:
            if on_screen_rect((car.pos[0] - 40, car.pos[1] - 40, 80, 80), self.cam, SCREEN_W, SCREEN_H):
                car.draw(self.screen, self.cam)
        for group in (self.civilians, self.enemies, self.police):
            for actor in group:
                if actor.alive and on_screen_rect((actor.pos[0] - 24, actor.pos[1] - 24, 48, 48), self.cam, SCREEN_W, SCREEN_H):
                    actor.draw(self.screen, self.cam)
        for b in self.bullets:
            b.draw(self.screen, self.cam)
        for p in self.particles:
            p.draw(self.screen, self.cam)
        self.player.draw(self.screen, self.cam)
        for d in self.damage_numbers:
            d.draw(self.screen, self.cam, self.font_small)
        self.environment.draw_overlay(self.screen)
        self.draw_hud()
        if self.game_over:
            self.draw_game_over()
        pygame.display.flip()

    def draw_menu(self):
        self.screen.fill((19, 38, 45))
        title = self.font_large.render("GANGSTER CITY", True, YELLOW)
        sub = self.font_medium.render("Your city progress auto-loads until Clear Database", True, WHITE)
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, SCREEN_H // 2 - 180))
        self.screen.blit(sub, (SCREEN_W // 2 - sub.get_width() // 2, SCREEN_H // 2 - 126))
        for rect, label in (
            (self.start_button, "START / CONTINUE"),
            (self.mission_log_button, "MISSION LOG"),
            (self.save_quit_button, "SAVE & QUIT"),
            (self.clear_button, "CLEAR DATABASE"),
            (self.quit_button, "QUIT WITHOUT SAVING"),
        ):
            hover = rect.collidepoint(pygame.mouse.get_pos())
            pygame.draw.rect(self.screen, (45, 105, 85) if hover else (35, 75, 70), rect, border_radius=6)
            pygame.draw.rect(self.screen, WHITE, rect, 2, border_radius=6)
            txt = self.font_medium.render(label, True, WHITE)
            self.screen.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))
        hint = self.font_small.render("Enter start   M mission log   S save & quit   C clear database   F fullscreen   Q/Esc quit", True, (200, 205, 205))
        self.screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H // 2 + 270))

    def draw_hud(self):
        pygame.draw.rect(self.screen, (0, 0, 0), (0, SCREEN_H - 96, SCREEN_W, 96))
        self.draw_weapon_icon()
        hp = self.player.health / self.player.max_health
        pygame.draw.rect(self.screen, (50, 50, 50), (14, SCREEN_H - 82, 170, 18))
        pygame.draw.rect(self.screen, (int(255 * (1 - hp)), int(220 * hp), 40), (14, SCREEN_H - 82, int(170 * hp), 18))
        armor = min(1, self.player.armor / 150) if self.player.armor else 0
        pygame.draw.rect(self.screen, (45, 45, 55), (14, SCREEN_H - 58, 170, 12))
        pygame.draw.rect(self.screen, BLUE, (14, SCREEN_H - 58, int(170 * armor), 12))
        weapon = self.font_small.render(f"City: {self.city_name()}   Weapon: {self.player.weapon}   Money: ${self.player.money}   Rep: {self.player.reputation}", True, WHITE)
        self.screen.blit(weapon, (210, SCREEN_H - 82))
        m = self.missions.current
        mission_text = "Story complete" if not m else f"Mission: {m.title} - {m.objective}"
        self.screen.blit(self.font_small.render(mission_text, True, YELLOW), (210, SCREEN_H - 58))
        wanted = "Neutral"
        if self.wanted.level:
            wanted = f"WANTED {self.wanted.level}  {int(self.wanted.timer)}s"
        self.screen.blit(self.font_medium.render(wanted, True, RED if self.wanted.level else GREEN), (SCREEN_W - 235, SCREEN_H - 84))
        weather = f"{int(self.environment.time):02d}:00  {self.environment.weather}"
        self.screen.blit(self.font_small.render(weather, True, WHITE), (SCREEN_W - 235, SCREEN_H - 48))
        controls = self.font_small.render("E car/interact  Z building  M map  H hospital  G garage  B bank  F fullscreen  1-9 weapons", True, (190, 190, 190))
        self.screen.blit(controls, (14, SCREEN_H - 28))
        self.draw_minimap()
        if self.toast_timer > 0 and self.toast:
            box = pygame.Surface((SCREEN_W, 34), pygame.SRCALPHA)
            box.fill((0, 0, 0, 155))
            self.screen.blit(box, (0, 16))
            txt = self.font_medium.render(self.toast, True, WHITE)
            self.screen.blit(txt, (SCREEN_W // 2 - txt.get_width() // 2, 21))

    def draw_weapon_icon(self):
        panel = pygame.Rect(14, 14, 92, 72)
        pygame.draw.rect(self.screen, (8, 8, 10), panel)
        pygame.draw.rect(self.screen, WHITE, panel, 2)
        cx, cy = panel.centerx, panel.centery - 4
        weapon = self.player.weapon
        if weapon == "None":
            pygame.draw.circle(self.screen, (205, 145, 95), (cx - 8, cy), 9)
            pygame.draw.circle(self.screen, (205, 145, 95), (cx + 8, cy), 9)
            pygame.draw.rect(self.screen, (205, 145, 95), (cx - 18, cy + 8, 36, 10), border_radius=4)
            label = "HAND"
        elif weapon == "Pistol":
            pygame.draw.rect(self.screen, (80, 80, 85), (cx - 23, cy - 5, 38, 10))
            pygame.draw.rect(self.screen, (45, 45, 48), (cx + 8, cy + 3, 10, 20))
            label = "PISTOL"
        elif weapon == "Shotgun":
            pygame.draw.rect(self.screen, (85, 62, 35), (cx - 34, cy - 4, 58, 8))
            pygame.draw.rect(self.screen, (50, 50, 54), (cx + 22, cy - 5, 18, 10))
            label = "SHOTGUN"
        elif weapon == "Rifle":
            pygame.draw.rect(self.screen, (60, 60, 62), (cx - 36, cy - 4, 70, 8))
            pygame.draw.rect(self.screen, (95, 70, 40), (cx - 18, cy + 4, 24, 9))
            label = "RIFLE"
        elif weapon == "SMG":
            pygame.draw.rect(self.screen, (70, 70, 76), (cx - 25, cy - 5, 42, 9))
            pygame.draw.rect(self.screen, (35, 35, 38), (cx - 2, cy + 3, 10, 18))
            label = "SMG"
        elif weapon == "Heavy Rifle":
            pygame.draw.rect(self.screen, (50, 50, 54), (cx - 38, cy - 5, 74, 10))
            pygame.draw.rect(self.screen, (110, 85, 45), (cx - 20, cy + 5, 28, 10))
            label = "HEAVY"
        elif weapon == "Combat Shotgun":
            pygame.draw.rect(self.screen, (92, 64, 35), (cx - 36, cy - 5, 66, 10))
            pygame.draw.rect(self.screen, (35, 35, 38), (cx + 20, cy - 7, 20, 14))
            label = "C-SHOT"
        elif weapon == "Rocket Launcher":
            pygame.draw.rect(self.screen, (65, 92, 65), (cx - 36, cy - 8, 72, 16), border_radius=6)
            pygame.draw.circle(self.screen, BLACK, (cx + 34, cy), 8, 2)
            label = "ROCKET"
        else:
            pygame.draw.circle(self.screen, (45, 95, 45), (cx, cy), 13)
            pygame.draw.circle(self.screen, BLACK, (cx, cy), 13, 2)
            label = f"GRENADE x{self.player.grenades}"
        txt = self.font_small.render(label, True, YELLOW)
        self.screen.blit(txt, (panel.centerx - txt.get_width() // 2, panel.bottom - 19))

    def draw_minimap(self):
        minimap_w, minimap_h = 220, 150
        minimap_x, minimap_y = SCREEN_W - minimap_w - 14, 14
        scale_x = minimap_w / MAP_W
        scale_y = minimap_h / MAP_H
        pygame.draw.rect(self.screen, (8, 10, 12), (minimap_x, minimap_y, minimap_w, minimap_h))
        pygame.draw.rect(self.screen, WHITE, (minimap_x, minimap_y, minimap_w, minimap_h), 2)

        for road in self.city.roads:
            x, y, w, h = road
            pygame.draw.rect(self.screen, (58, 58, 62),
                             (minimap_x + int(x * scale_x), minimap_y + int(y * scale_y),
                              max(1, int(w * scale_x)), max(1, int(h * scale_y))))

        m = self.missions.current
        if m:
            mx = minimap_x + int(m.marker[0] * scale_x)
            my = minimap_y + int(m.marker[1] * scale_y)
            pygame.draw.circle(self.screen, YELLOW, (mx, my), 4)

        for car in self.cars[:30] + self.traffic[:30]:
            cx = minimap_x + int(car.pos[0] * scale_x)
            cy = minimap_y + int(car.pos[1] * scale_y)
            pygame.draw.circle(self.screen, (160, 160, 170), (cx, cy), 1)

        service_letters = {
            "bank": ("B", YELLOW),
            "hospital": ("H", WHITE),
            "police": ("P", BLUE),
            "gunshop": ("G", (255, 150, 80)),
            "airport": ("A", (120, 220, 255)),
        }
        seen = set()
        for building in self.city.landmarks + self.city.buildings:
            if building.kind not in service_letters:
                continue
            center = (int(building.rect[0] + building.rect[2] / 2), int(building.rect[1] + building.rect[3] / 2))
            key = (building.kind, center)
            if key in seen:
                continue
            seen.add(key)
            letter, color = service_letters[building.kind]
            bx = minimap_x + int(center[0] * scale_x)
            by = minimap_y + int(center[1] * scale_y)
            txt = self.font_small.render(letter, True, color)
            self.screen.blit(txt, (bx - txt.get_width() // 2, by - txt.get_height() // 2))

        for civ in self.civilians:
            if civ.alive:
                cx = minimap_x + int(civ.pos[0] * scale_x)
                cy = minimap_y + int(civ.pos[1] * scale_y)
                pygame.draw.circle(self.screen, GREEN, (cx, cy), 1)

        for enemy in self.enemies:
            if enemy.alive:
                ex = minimap_x + int(enemy.pos[0] * scale_x)
                ey = minimap_y + int(enemy.pos[1] * scale_y)
                pygame.draw.circle(self.screen, RED, (ex, ey), 2)

        for cop in self.police:
            if cop.alive:
                px = minimap_x + int(cop.pos[0] * scale_x)
                py = minimap_y + int(cop.pos[1] * scale_y)
                pygame.draw.circle(self.screen, BLUE, (px, py), 2)

        px = minimap_x + int(self.player.pos[0] * scale_x)
        py = minimap_y + int(self.player.pos[1] * scale_y)
        pygame.draw.circle(self.screen, WHITE, (px, py), 4)
        label = self.font_small.render("MAP", True, WHITE)
        self.screen.blit(label, (minimap_x + 8, minimap_y + 6))

    def draw_full_map(self):
        self.screen.fill((9, 14, 18))
        margin = 54
        map_w, map_h = SCREEN_W - margin * 2, SCREEN_H - 128
        map_x, map_y = margin, 70
        scale_x = map_w / MAP_W
        scale_y = map_h / MAP_H
        pygame.draw.rect(self.screen, (18, 24, 28), (map_x, map_y, map_w, map_h))
        pygame.draw.rect(self.screen, WHITE, (map_x, map_y, map_w, map_h), 2)

        title = self.font_large.render(f"{self.city_name().upper()} MAP", True, YELLOW)
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 18))

        for d in self.city.districts:
            x, y, w, h = d.rect
            rect = pygame.Rect(map_x + int(x * scale_x), map_y + int(y * scale_y), max(2, int(w * scale_x)), max(2, int(h * scale_y)))
            pygame.draw.rect(self.screen, d.ground, rect)
            pygame.draw.rect(self.screen, (28, 34, 38), rect, 1)
            label = self.font_small.render(d.name, True, WHITE)
            self.screen.blit(label, (rect.x + 6, rect.y + 6))

        for road in self.city.roads:
            x, y, w, h = road
            pygame.draw.rect(self.screen, (72, 72, 76), (map_x + int(x * scale_x), map_y + int(y * scale_y), max(1, int(w * scale_x)), max(1, int(h * scale_y))))

        service_letters = {
            "bank": ("B", YELLOW),
            "hospital": ("H", WHITE),
            "police": ("P", BLUE),
            "gunshop": ("G", (255, 150, 80)),
            "garage": ("R", (170, 170, 170)),
            "gas": ("S", (255, 90, 70)),
            "airport": ("A", (120, 220, 255)),
        }
        for building in self.city.landmarks:
            if building.kind not in service_letters:
                continue
            letter, color = service_letters[building.kind]
            bx = map_x + int((building.rect[0] + building.rect[2] / 2) * scale_x)
            by = map_y + int((building.rect[1] + building.rect[3] / 2) * scale_y)
            pygame.draw.circle(self.screen, (8, 8, 10), (bx, by), 10)
            pygame.draw.circle(self.screen, color, (bx, by), 10, 2)
            txt = self.font_small.render(letter, True, color)
            self.screen.blit(txt, (bx - txt.get_width() // 2, by - txt.get_height() // 2))

        m = self.missions.current
        if m:
            mx = map_x + int(m.marker[0] * scale_x)
            my = map_y + int(m.marker[1] * scale_y)
            pygame.draw.circle(self.screen, YELLOW, (mx, my), 15, 3)
            pygame.draw.circle(self.screen, YELLOW, (mx, my), 4)
            label = self.font_small.render("MISSION", True, YELLOW)
            self.screen.blit(label, (mx + 12, my - 8))

        px = map_x + int(self.player.pos[0] * scale_x)
        py = map_y + int(self.player.pos[1] * scale_y)
        pygame.draw.circle(self.screen, WHITE, (px, py), 7)
        pygame.draw.circle(self.screen, BLACK, (px, py), 7, 2)
        player_label = self.font_small.render("YOU", True, WHITE)
        self.screen.blit(player_label, (px + 10, py - 8))

        legend = "A airport   B bank   H hospital   P police   G gun shop   R garage   S gas   M/Esc close"
        hint = self.font_small.render(legend, True, (210, 215, 215))
        self.screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H - 38))

    def draw_mission_log(self):
        self.screen.fill((14, 19, 23))
        title = self.font_large.render(f"{self.city_name().upper()} MISSION LOG", True, YELLOW)
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 28))
        subtitle = self.font_small.render("Completed missions are marked DONE. Click, Enter, M, or Esc to return.", True, (205, 210, 210))
        self.screen.blit(subtitle, (SCREEN_W // 2 - subtitle.get_width() // 2, 72))

        start_y = 116
        row_h = 28
        for i, mission in enumerate(self.missions.missions):
            y = start_y + i * row_h
            if y > SCREEN_H - 54:
                break
            if i < self.missions.index:
                status, color = "DONE", GREEN
            elif i == self.missions.index:
                status, color = "ACTIVE", YELLOW
            else:
                status, color = "LOCKED", (140, 145, 150)
            bg = (26, 36, 40) if i == self.missions.index else (18, 24, 28)
            pygame.draw.rect(self.screen, bg, (76, y - 4, SCREEN_W - 152, row_h - 2))
            pygame.draw.rect(self.screen, (55, 65, 68), (76, y - 4, SCREEN_W - 152, row_h - 2), 1)
            status_txt = self.font_small.render(status, True, color)
            self.screen.blit(status_txt, (92, y))
            title_txt = self.font_small.render(f"{i + 1}. {mission.title}", True, WHITE if i <= self.missions.index else (165, 170, 175))
            self.screen.blit(title_txt, (170, y))
            obj_txt = self.font_small.render(mission.objective, True, (205, 205, 190) if i <= self.missions.index else (125, 130, 135))
            self.screen.blit(obj_txt, (430, y))
    def draw_gunshop(self):
        self.screen.fill((34, 31, 29))
        pygame.draw.rect(self.screen, (56, 48, 42), (0, SCREEN_H - 150, SCREEN_W, 150))
        pygame.draw.rect(self.screen, (88, 70, 50), (110, 155, SCREEN_W - 220, 90))
        pygame.draw.rect(self.screen, (22, 22, 24), (150, 210, SCREEN_W - 300, 18))
        pygame.draw.rect(self.screen, (70, 55, 40), (150, 250, SCREEN_W - 300, 210))
        for i in range(5):
            y = 285 + i * 34
            pygame.draw.line(self.screen, (35, 35, 35), (180, y), (SCREEN_W - 180, y), 4)
            pygame.draw.rect(self.screen, (105, 105, 110), (220 + i * 120, y - 12, 76, 7))
            pygame.draw.rect(self.screen, (45, 45, 48), (285 + i * 120, y - 10, 22, 11))

        title = self.font_large.render("GUN SHOP", True, YELLOW)
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 64))
        money = self.font_medium.render(f"Money: ${self.player.money}", True, WHITE)
        self.screen.blit(money, (SCREEN_W // 2 - money.get_width() // 2, 112))

        panel_h = 190 if len(self.gunshop_items) > 5 else 155
        panel = pygame.Rect(SCREEN_W // 2 - 230, SCREEN_H - panel_h - 72, 460, panel_h)
        pygame.draw.rect(self.screen, (12, 12, 14), panel)
        pygame.draw.rect(self.screen, WHITE, panel, 2)
        for i, (item, price) in enumerate(self.gunshop_items):
            y = panel.y + 16 + i * 25
            color = YELLOW if i == self.gunshop_selection else WHITE
            prefix = ">" if i == self.gunshop_selection else " "
            line = self.font_medium.render(f"{prefix} {i+1}. {item}  ${price}", True, color)
            self.screen.blit(line, (panel.x + 28, y))

        hint = self.font_small.render("W/S or arrows select   Enter buy   E/Esc exit", True, (210, 210, 210))
        self.screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H - 60))

    def draw_interior(self):
        b = self.current_building
        kind = b.kind if b else "building"
        palettes = {
            "bank": ((38, 48, 54), (130, 112, 72), "BANK"),
            "hospital": ((218, 222, 218), (95, 150, 170), "HOSPITAL"),
            "police": ((40, 58, 86), (72, 105, 160), "POLICE STATION"),
            "gunshop": ((34, 31, 29), (110, 72, 54), "GUN SHOP"),
            "store": ((62, 58, 48), (130, 90, 55), "SHOP"),
            "restaurant": ((74, 45, 42), (145, 70, 55), "RESTAURANT"),
            "garage": ((46, 48, 50), (96, 96, 92), "GARAGE"),
            "gas": ((55, 50, 45), (160, 60, 50), "GAS SHOP"),
            "office": ((42, 50, 58), (75, 105, 125), "OFFICE"),
            "apartment": ((58, 50, 45), (120, 90, 70), "APARTMENT"),
            "villa": ((62, 75, 55), (165, 145, 105), "VILLA"),
            "factory": ((54, 52, 48), (110, 100, 82), "FACTORY"),
            "warehouse": ((50, 50, 52), (100, 95, 85), "WAREHOUSE"),
            "slum": ((58, 48, 38), (115, 80, 55), "HOUSE"),
        }
        palettes["airport"] = ((42, 48, 54), (125, 128, 135), "AIRPORT")
        bg, accent, title_text = palettes.get(kind, ((48, 48, 50), (95, 95, 95), "BUILDING"))
        self.screen.fill(bg)
        pygame.draw.rect(self.screen, accent, (70, 95, SCREEN_W - 140, SCREEN_H - 190))
        pygame.draw.rect(self.screen, BLACK, (95, 125, SCREEN_W - 190, SCREEN_H - 250), 4)
        pygame.draw.rect(self.screen, (28, 28, 30), (130, 160, SCREEN_W - 260, 32))
        pygame.draw.rect(self.screen, (78, 58, 42), (170, 470, SCREEN_W - 340, 58))
        for x in range(190, SCREEN_W - 190, 110):
            pygame.draw.rect(self.screen, (45, 45, 48), (x, 215, 70, 12))
            pygame.draw.rect(self.screen, (85, 85, 88), (x + 8, 228, 48, 34))
        if kind == "hospital":
            pygame.draw.rect(self.screen, WHITE, (SCREEN_W // 2 - 10, 220, 20, 70))
            pygame.draw.rect(self.screen, RED, (SCREEN_W // 2 - 40, 245, 80, 20))
        elif kind == "police":
            pygame.draw.rect(self.screen, BLUE, (SCREEN_W // 2 - 90, 220, 180, 50))
            pygame.draw.rect(self.screen, WHITE, (SCREEN_W // 2 - 35, 234, 70, 22))
        elif kind == "bank":
            pygame.draw.rect(self.screen, (170, 150, 90), (SCREEN_W // 2 - 140, 218, 280, 80))
            pygame.draw.circle(self.screen, YELLOW, (SCREEN_W // 2, 258), 22)
        elif kind == "airport":
            pygame.draw.rect(self.screen, (80, 88, 96), (SCREEN_W // 2 - 220, 220, 440, 74))
            pygame.draw.rect(self.screen, WHITE, (SCREEN_W // 2 - 180, 245, 360, 8))
            pygame.draw.polygon(self.screen, (190, 200, 210), [(SCREEN_W // 2 - 20, 245), (SCREEN_W // 2 + 80, 225), (SCREEN_W // 2 + 80, 265)])
        elif kind == "gunshop":
            for i in range(5):
                y = 230 + i * 32
                pygame.draw.line(self.screen, (35, 35, 35), (220, y), (SCREEN_W - 220, y), 4)
                pygame.draw.rect(self.screen, (105, 105, 110), (260 + i * 110, y - 12, 76, 7))

        title = self.font_large.render(f"{b.label if b else title_text} INTERIOR", True, YELLOW)
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 36))
        money = self.font_medium.render(f"Money: ${self.player.money}", True, WHITE)
        self.screen.blit(money, (SCREEN_W // 2 - money.get_width() // 2, 82))

        items = self.interior_items()
        if items:
            panel_h = max(145, 20 + len(items) * 25)
            panel = pygame.Rect(SCREEN_W // 2 - 250, SCREEN_H - panel_h - 60, 500, panel_h)
            pygame.draw.rect(self.screen, (10, 10, 12), panel)
            pygame.draw.rect(self.screen, WHITE, panel, 2)
            for i, (item, price) in enumerate(items):
                y = panel.y + 16 + i * 25
                color = YELLOW if i == self.interior_selection else WHITE
                prefix = ">" if i == self.interior_selection else " "
                cost = "FREE" if price == 0 else f"${price}"
                line = self.font_medium.render(f"{prefix} {i+1}. {item}  {cost}", True, color)
                self.screen.blit(line, (panel.x + 22, y))
            hint = "W/S select   Enter/E buy/use   Z/Esc exit"
        else:
            msg = self.font_medium.render("No services here. Use this as a hideout.", True, WHITE)
            self.screen.blit(msg, (SCREEN_W // 2 - msg.get_width() // 2, SCREEN_H - 150))
            hint = "Z/Esc exit"
        hint_txt = self.font_small.render(hint, True, (215, 215, 215))
        self.screen.blit(hint_txt, (SCREEN_W // 2 - hint_txt.get_width() // 2, SCREEN_H - 34))

    def draw_game_over(self):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 165))
        self.screen.blit(overlay, (0, 0))
        title = self.font_large.render("GAME OVER", True, RED)
        hint = self.font_medium.render("Press R to restart or Esc for menu", True, WHITE)
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, SCREEN_H // 2 - 55))
        self.screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H // 2 + 5))

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000
            self.events()
            self.update(dt)
            self.draw()
        pygame.quit()


def main():
    Game().run()









