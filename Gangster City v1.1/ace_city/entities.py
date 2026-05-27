import math
import random
import pygame
from .config import BLACK, BLUE, BULLET_SPEED, GREEN, MAP_H, MAP_W, PLAYER_SPEED, RED, WHITE, YELLOW
from .utils import dist, keep_inside_map, normalize, resolve_aabb
from .sprites import civilian_sprite, draw_shadow, enemy_sprite, player_sprite, police_sprite, rotate_draw


class Bullet:
    def __init__(self, pos, vel, owner, damage, color):
        self.pos = list(pos)
        self.vel = list(vel)
        self.owner = owner
        self.damage = damage
        self.color = color
        self.life = 1.4

    def update(self, dt):
        self.pos[0] += self.vel[0] * dt
        self.pos[1] += self.vel[1] * dt
        self.life -= dt
        return self.life > 0

    def draw(self, surf, cam):
        x, y = int(self.pos[0] - cam[0]), int(self.pos[1] - cam[1])
        pygame.draw.circle(surf, self.color, (x, y), 5)
        pygame.draw.circle(surf, WHITE, (x, y), 2)


class Grenade:
    def __init__(self, pos, vel, owner="player"):
        self.pos = list(pos)
        self.vel = list(vel)
        self.owner = owner
        self.damage = 70
        self.radius = 95
        self.life = 0.9
        self.exploded = False

    def update(self, dt):
        self.pos[0] += self.vel[0] * dt
        self.pos[1] += self.vel[1] * dt
        self.vel[0] *= 0.94
        self.vel[1] *= 0.94
        self.life -= dt
        return self.life > 0

    def draw(self, surf, cam):
        x, y = int(self.pos[0] - cam[0]), int(self.pos[1] - cam[1])
        pygame.draw.circle(surf, (45, 95, 45), (x, y), 7)
        pygame.draw.circle(surf, BLACK, (x, y), 7, 2)


class Player:
    def __init__(self, x, y):
        self.pos = [x, y]
        self.size = 16
        self.sprite = player_sprite()
        self.health = 100
        self.max_health = 100
        self.armor = 0
        self.money = 40
        self.in_car = None
        self.direction = 0
        self.weapon_order = ["None", "Pistol", "Shotgun", "Rifle", "SMG", "Heavy Rifle", "Combat Shotgun", "Rocket Launcher", "Grenade"]
        self.weapons = {"None": None}
        self.weapon = "None"
        self.grenades = 0
        self.cooldown = 0
        self.noise_timer = 0
        self.reputation = 0

    def unlock_weapon(self, name):
        stats = {
            "Pistol": {"damage": 30, "cooldown": 0.32, "pellets": 1, "spread": 0.0},
            "Shotgun": {"damage": 21, "cooldown": 0.78, "pellets": 5, "spread": 0.38},
            "Rifle": {"damage": 18, "cooldown": 0.11, "pellets": 1, "spread": 0.03},
            "SMG": {"damage": 16, "cooldown": 0.07, "pellets": 1, "spread": 0.07},
            "Heavy Rifle": {"damage": 32, "cooldown": 0.16, "pellets": 1, "spread": 0.02},
            "Combat Shotgun": {"damage": 26, "cooldown": 0.55, "pellets": 6, "spread": 0.25},
            "Rocket Launcher": {"damage": 120, "cooldown": 1.1, "pellets": 1, "spread": 0.0},
            "Grenade": {"damage": 70, "cooldown": 0.8, "pellets": 1, "spread": 0.0},
        }
        if name in stats:
            self.weapons[name] = stats[name]
            self.weapon = name

    def update(self, dt, city):
        self.cooldown -= dt
        self.noise_timer = max(0, self.noise_timer - dt)
        if self.in_car:
            self.pos = self.in_car.pos[:]
            return
        keys = pygame.key.get_pressed()
        mx = keys[pygame.K_d] - keys[pygame.K_a]
        my = keys[pygame.K_s] - keys[pygame.K_w]
        if mx or my:
            nx, ny = normalize((mx, my))
            self.direction = math.atan2(ny, nx)
            self.pos[0] += nx * PLAYER_SPEED * dt
            self.pos[1] += ny * PLAYER_SPEED * dt
        for r in city.collision_rects_near(self.pos):
            resolve_aabb(self.pos, self.size, r)
        keep_inside_map(self.pos, 20, MAP_W, MAP_H)

    def switch_weapon(self, index):
        if 0 <= index < len(self.weapon_order):
            name = self.weapon_order[index]
            if name == "None" or name in self.weapons:
                self.weapon = name

    def shoot(self, tx, ty, bullets):
        stats = self.weapons.get(self.weapon)
        if not stats or self.cooldown > 0:
            return False
        nd = normalize((tx - self.pos[0], ty - self.pos[1]))
        if nd == (0, 0):
            return False
        self.direction = math.atan2(nd[1], nd[0])
        self.noise_timer = 4.0
        if self.weapon == "Rocket Launcher":
            bullets.append(Grenade(self.pos, (nd[0] * 680, nd[1] * 680)))
            bullets[-1].damage = 120
            bullets[-1].radius = 135
            bullets[-1].life = 0.55
            self.cooldown = stats["cooldown"]
            return True
        if self.weapon == "Grenade":
            if self.grenades <= 0:
                return False
            self.grenades -= 1
            bullets.append(Grenade(self.pos, (nd[0] * 520, nd[1] * 520)))
            self.cooldown = stats["cooldown"]
            return True
        for _ in range(stats["pellets"]):
            angle = self.direction + random.uniform(-stats["spread"], stats["spread"])
            bullets.append(Bullet(self.pos, (math.cos(angle) * BULLET_SPEED, math.sin(angle) * BULLET_SPEED), "player", stats["damage"], YELLOW))
        self.cooldown = stats["cooldown"]
        return True

    def take_damage(self, amount):
        absorbed = min(self.armor, amount * 0.55)
        self.armor -= absorbed
        self.health -= amount - absorbed

    def draw(self, surf, cam):
        if self.in_car:
            return
        x, y = self.pos[0] - cam[0], self.pos[1] - cam[1]
        draw_shadow(surf, x, y, 16)
        rotate_draw(surf, self.sprite, (x, y), self.direction)


class Actor:
    def __init__(self, x, y, sprite, health=50):
        self.pos = [x, y]
        self.sprite = sprite
        self.health = health
        self.alive = True
        self.direction = random.random() * math.tau
        self.timer = random.random()
        self.state = "idle"

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.alive = False

    def draw(self, surf, cam):
        if not self.alive:
            return
        x, y = self.pos[0] - cam[0], self.pos[1] - cam[1]
        draw_shadow(surf, x, y, 12)
        rotate_draw(surf, self.sprite, (x, y), self.direction)


class Enemy(Actor):
    def __init__(self, x, y, elite=False):
        super().__init__(x, y, enemy_sprite(), 115 if elite else 70)
        self.elite = elite
        self.role = random.choice(["patrol", "flank", "guard"])
        self.shoot_timer = random.uniform(0.3, 1.4)

    def update(self, dt, player, city, bullets, combat_alert):
        if not self.alive:
            return
        d = dist(self.pos, player.pos)
        aggro = combat_alert or d < 170
        if aggro and d < 720:
            dx, dy = player.pos[0] - self.pos[0], player.pos[1] - self.pos[1]
            nd = normalize((dx, dy))
            if self.role == "flank":
                nd = normalize((nd[0] * 0.65 - nd[1] * 0.55, nd[1] * 0.65 + nd[0] * 0.55))
            speed = (180 if self.elite else 145) if d > 260 else -70
            self.direction = math.atan2(player.pos[1] - self.pos[1], player.pos[0] - self.pos[0])
            self.pos[0] += nd[0] * speed * dt
            self.pos[1] += nd[1] * speed * dt
            self.shoot_timer -= dt
            if self.shoot_timer <= 0 and d < 520:
                damage = 13 if self.elite else 8
                bullet_speed = 650 if self.elite else 530
                bullets.append(Bullet(self.pos, (math.cos(self.direction) * bullet_speed, math.sin(self.direction) * bullet_speed), "enemy", damage, RED))
                self.shoot_timer = random.uniform(0.55, 1.15) if self.elite else random.uniform(1.0, 1.8)
        else:
            self.patrol(dt)
        self.collide(city)

    def patrol(self, dt):
        self.timer -= dt
        if self.timer <= 0:
            self.direction = random.random() * math.tau
            self.timer = random.uniform(1, 3)
        self.pos[0] += math.cos(self.direction) * 55 * dt
        self.pos[1] += math.sin(self.direction) * 55 * dt

    def collide(self, city):
        for r in city.collision_rects_near(self.pos):
            resolve_aabb(self.pos, 12, r)
        keep_inside_map(self.pos, 20, MAP_W, MAP_H)


class Police(Actor):
    def __init__(self, x, y):
        super().__init__(x, y, police_sprite(), 85)
        self.shoot_timer = 0.8

    def update(self, dt, player, city, bullets, wanted_level, enemies):
        if not self.alive:
            return
        target = None
        if wanted_level > 0:
            target = player
        else:
            living = [e for e in enemies if e.alive and dist(e.pos, self.pos) < 520]
            if living:
                target = min(living, key=lambda e: dist(e.pos, self.pos))
        if target:
            d = dist(self.pos, target.pos)
            nd = normalize((target.pos[0] - self.pos[0], target.pos[1] - self.pos[1]))
            self.direction = math.atan2(nd[1], nd[0])
            if d > 180:
                self.pos[0] += nd[0] * 185 * dt
                self.pos[1] += nd[1] * 185 * dt
            self.shoot_timer -= dt
            if self.shoot_timer <= 0 and d < 470:
                bullets.append(Bullet(self.pos, (nd[0] * 560, nd[1] * 560), "police", 12, BLUE))
                self.shoot_timer = 1.05
        else:
            Enemy.patrol(self, dt)
        for r in city.collision_rects_near(self.pos):
            resolve_aabb(self.pos, 12, r)
        keep_inside_map(self.pos, 20, MAP_W, MAP_H)


class Civilian(Actor):
    def __init__(self, x, y):
        super().__init__(x, y, civilian_sprite(), 35)
        self.panic = 0

    def update(self, dt, player, city, combat_alert):
        if not self.alive:
            return
        d = dist(self.pos, player.pos)
        if combat_alert and d < 520:
            self.panic = 3.5
        if self.panic > 0:
            self.panic -= dt
            nd = normalize((self.pos[0] - player.pos[0], self.pos[1] - player.pos[1]))
            self.direction = math.atan2(nd[1], nd[0])
            speed = 175
        else:
            self.timer -= dt
            if self.timer <= 0:
                self.direction = random.random() * math.tau
                self.timer = random.uniform(0.8, 2.7)
            nd = (math.cos(self.direction), math.sin(self.direction))
            speed = 48
        self.pos[0] += nd[0] * speed * dt
        self.pos[1] += nd[1] * speed * dt
        for r in city.collision_rects_near(self.pos):
            resolve_aabb(self.pos, 12, r)
        keep_inside_map(self.pos, 20, MAP_W, MAP_H)


class Vehicle:
    def __init__(self, x, y, color=(150, 35, 35), traffic=False, model=None):
        self.pos = [x, y]
        self.angle = random.choice([0, math.pi / 2, math.pi, -math.pi / 2])
        self.speed = 0
        self.driver = None
        self.color = color
        self.health = 180
        self.traffic = traffic
        self.model = model or random.choice(["sedan", "sport", "truck", "taxi", "van", "police"])
        self.turn_timer = random.uniform(1, 4)
        specs = {
            "sedan": (520, 520, 2.5, (52, 30)),
            "sport": (680, 610, 3.2, (56, 28)),
            "truck": (390, 430, 1.7, (66, 36)),
            "taxi": (500, 500, 2.3, (54, 30)),
            "van": (430, 455, 1.9, (62, 34)),
            "police": (590, 560, 2.7, (56, 30)),
            "supercar": (880, 780, 3.9, (60, 28)),
            "street_racer": (760, 720, 3.8, (58, 28)),
            "armored_suv": (560, 610, 2.4, (70, 38)),
            "luxury": (650, 640, 3.0, (62, 32)),
            "black_van": (520, 560, 2.1, (68, 36)),
            "tuned_police": (760, 720, 3.4, (58, 30)),
        }
        self.max_speed, self.accel, self.handling, self.size = specs[self.model]

    def update(self, dt, city):
        if self.driver:
            keys = pygame.key.get_pressed()
            accel = (keys[pygame.K_w] - keys[pygame.K_s]) * self.accel
            steer = (keys[pygame.K_d] - keys[pygame.K_a]) * self.handling
            self.speed += accel * dt
            self.speed *= 0.985
            self.speed = max(-180, min(self.max_speed, self.speed))
            if abs(self.speed) > 35:
                self.angle += steer * dt * (1 if self.speed > 0 else -1)
        elif self.traffic:
            self.speed = min(155, self.max_speed * 0.35)
            self.turn_timer -= dt
            if self.turn_timer <= 0:
                self.angle += random.choice([-math.pi / 2, 0, math.pi / 2])
                self.turn_timer = random.uniform(2.5, 6)
        else:
            self.speed *= 0.96
        old = self.pos[:]
        self.pos[0] += math.cos(self.angle) * self.speed * dt
        self.pos[1] += math.sin(self.angle) * self.speed * dt
        for r in city.collision_rects_near(self.pos, 180):
            if r[0] - 22 < self.pos[0] < r[0] + r[2] + 22 and r[1] - 18 < self.pos[1] < r[1] + r[3] + 18:
                self.pos = old
                self.speed *= -0.25
                break
        keep_inside_map(self.pos, 30, MAP_W, MAP_H)
        if self.driver:
            self.driver.pos = self.pos[:]

    def draw(self, surf, cam):
        x, y = self.pos[0] - cam[0], self.pos[1] - cam[1]
        w, h = self.size
        car = pygame.Surface((w, h), pygame.SRCALPHA)
        body_color = (220, 185, 55) if self.model == "taxi" else (35, 70, 165) if self.model in ("police", "tuned_police") else (18, 18, 24) if self.model == "black_van" else (185, 185, 205) if self.model == "luxury" else (180, 40, 55) if self.model in ("supercar", "street_racer") else self.color
        pygame.draw.rect(car, body_color, (4, 5, w - 8, h - 10), border_radius=5)
        pygame.draw.rect(car, (100, 180, 230), (int(w * 0.25), 7, int(w * 0.18), 8))
        pygame.draw.rect(car, (100, 180, 230), (int(w * 0.55), 7, int(w * 0.18), 8))
        if self.model in ("police", "tuned_police"):
            pygame.draw.rect(car, (220, 40, 40), (w // 2 - 7, 3, 6, 4))
            pygame.draw.rect(car, (40, 100, 230), (w // 2 + 1, 3, 6, 4))
        if self.model in ("supercar", "street_racer"):
            pygame.draw.rect(car, (25, 25, 28), (8, h - 12, w - 16, 4))
            pygame.draw.rect(car, (240, 240, 245), (w // 2 - 5, 3, 10, 4))
        if self.model == "armored_suv":
            pygame.draw.rect(car, (35, 35, 38), (8, 8, w - 16, h - 16), 3)
        if self.model == "taxi":
            pygame.draw.rect(car, (20, 20, 20), (w // 2 - 7, 2, 14, 4))
        pygame.draw.circle(car, BLACK, (int(w * 0.27), h - 4), 5)
        pygame.draw.circle(car, BLACK, (int(w * 0.73), h - 4), 5)
        pygame.draw.circle(car, (255, 245, 160), (w - 5, 9), 3)
        pygame.draw.circle(car, (255, 245, 160), (w - 5, h - 9), 3)
        rotated = pygame.transform.rotate(car, -math.degrees(self.angle))
        surf.blit(rotated, rotated.get_rect(center=(x, y)))

