import math
import random
import pygame
from .config import BLACK, BLUE, FPS, GREEN, MAP_H, MAP_W, RED, SCREEN_H, SCREEN_W, WHITE, YELLOW
from .entities import Bullet, Civilian, Enemy, Player, Police, Vehicle
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
        self.city = City()
        self.environment = EnvironmentSystem()
        self.wanted = WantedSystem()
        self.audio = AudioSystem()
        self.missions = MissionSystem()
        self.state = "menu"
        self.running = True
        self.start_button = pygame.Rect(SCREEN_W // 2 - 140, SCREEN_H // 2 - 10, 280, 54)
        self.quit_button = pygame.Rect(SCREEN_W // 2 - 140, SCREEN_H // 2 + 60, 280, 54)
        self.reset_world()

    def reset_world(self):
        self.cam = [0, 0]
        self.player = Player(1280, 1450)
        self.cars = [Vehicle(*self.city.random_open_position(120, 25), color=random.choice([(150, 35, 35), (40, 80, 150), (210, 190, 80)])) for _ in range(24)]
        self.traffic = [Vehicle(*self.city.random_open_position(120, 25), color=(70, 70, 80), traffic=True) for _ in range(35)]
        self.enemies = [Enemy(*self.city.random_open_position(120, 18, random.choice(["Slums", "Industrial", "Market Mile"]))) for _ in range(30)]
        self.police = [Police(*self.city.random_open_position(120, 18, random.choice(["Civic Center", "Downtown"]))) for _ in range(18)]
        self.civilians = [Civilian(*self.city.random_open_position(120, 18)) for _ in range(85)]
        self.bullets = []
        self.particles = []
        self.damage_numbers = []
        self.mission_enemies = []
        self.spawn_timer = 15.0
        self.toast = "Story mode: start as nobody. Find the first mission marker."
        self.toast_timer = 5
        self.kills = 0
        self.civilians_hit = 0
        self.missions = MissionSystem()
        self.wanted = WantedSystem()
        self.game_over = False

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
        if random.random() < 0.55:
            self.enemies.append(Enemy(*self.city.random_open_position(120, 18, random.choice(["Slums", "Industrial"]))))
        elif random.random() < 0.72:
            self.police.append(Police(*self.city.random_open_position(120, 18, "Civic Center")))
        else:
            self.civilians.append(Civilian(*self.city.random_open_position(120, 18)))

    def events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            if self.state == "menu":
                self.menu_events(e)
                continue
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_f:
                    self.toggle_fullscreen()
                    continue
                if self.game_over and e.key == pygame.K_r:
                    self.reset_world()
                if e.key == pygame.K_ESCAPE:
                    self.state = "menu"
                if e.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                    self.player.switch_weapon(e.key - pygame.K_1)
                if e.key == pygame.K_e and not self.game_over:
                    self.interact()
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
                self.reset_world()
                self.state = "playing"
            elif e.key in (pygame.K_q, pygame.K_ESCAPE):
                self.running = False
        if e.type == pygame.MOUSEBUTTONDOWN:
            if self.start_button.collidepoint(e.pos):
                self.reset_world()
                self.state = "playing"
            elif self.quit_button.collidepoint(e.pos):
                self.running = False

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        flags = pygame.FULLSCREEN if self.fullscreen else 0
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), flags)

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
        self.try_service("store")

    def try_service(self, kind):
        near = [b for b in self.city.landmarks + self.city.buildings if b.kind == kind and dist((b.rect[0] + b.rect[2] / 2, b.rect[1] + b.rect[3] / 2), self.player.pos) < 180]
        if not near:
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

    def update(self, dt):
        if self.state == "menu":
            return
        self.environment.update(dt)
        self.wanted.update(dt)
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
            self.player.health = 0
            self.game_over = True

    def near_active(self, pos):
        return abs(pos[0] - self.player.pos[0]) < 1300 and abs(pos[1] - self.player.pos[1]) < 1000

    def update_bullets(self, dt):
        live = []
        remove = set()
        for b in self.bullets:
            if b.update(dt):
                live.append(b)
        self.bullets = live
        for b in self.bullets:
            if b.owner == "player":
                self.hit_group(b, self.enemies, remove, RED, reward=12)
                self.hit_group(b, self.police, remove, BLUE, crime="attacked police")
                self.hit_group(b, self.civilians, remove, RED, crime="hurt civilian", civilian=True)
            elif b.owner in ("enemy", "police"):
                if b.owner == "enemy":
                    self.hit_group(b, self.police, remove, BLUE)
                if dist(b.pos, self.player.pos) < 17:
                    self.player.take_damage(b.damage)
                    self.damage_numbers.append(DamageNumber(self.player.pos, b.damage, RED))
                    remove.add(b)
        self.bullets = [b for b in self.bullets if b not in remove]

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
                    for _ in range(10):
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
        sub = self.font_medium.render("Open-world story mode prototype", True, WHITE)
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, SCREEN_H // 2 - 150))
        self.screen.blit(sub, (SCREEN_W // 2 - sub.get_width() // 2, SCREEN_H // 2 - 96))
        for rect, label in ((self.start_button, "START GAME"), (self.quit_button, "QUIT GAME")):
            hover = rect.collidepoint(pygame.mouse.get_pos())
            pygame.draw.rect(self.screen, (45, 105, 85) if hover else (35, 75, 70), rect, border_radius=6)
            pygame.draw.rect(self.screen, WHITE, rect, 2, border_radius=6)
            txt = self.font_medium.render(label, True, WHITE)
            self.screen.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))
        hint = self.font_small.render("Enter/Space to start   F fullscreen   Q/Esc to quit", True, (200, 205, 205))
        self.screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H // 2 + 140))

    def draw_hud(self):
        pygame.draw.rect(self.screen, (0, 0, 0), (0, SCREEN_H - 96, SCREEN_W, 96))
        hp = self.player.health / self.player.max_health
        pygame.draw.rect(self.screen, (50, 50, 50), (14, SCREEN_H - 82, 170, 18))
        pygame.draw.rect(self.screen, (int(255 * (1 - hp)), int(220 * hp), 40), (14, SCREEN_H - 82, int(170 * hp), 18))
        armor = self.player.armor / 50 if self.player.armor else 0
        pygame.draw.rect(self.screen, (45, 45, 55), (14, SCREEN_H - 58, 170, 12))
        pygame.draw.rect(self.screen, BLUE, (14, SCREEN_H - 58, int(170 * armor), 12))
        weapon = self.font_small.render(f"Weapon: {self.player.weapon}   Money: ${self.player.money}   Rep: {self.player.reputation}", True, WHITE)
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
        controls = self.font_small.render("E enter/interact  H hospital  G garage  B bank  F fullscreen  1-4 weapons", True, (190, 190, 190))
        self.screen.blit(controls, (14, SCREEN_H - 28))
        if self.toast_timer > 0 and self.toast:
            box = pygame.Surface((SCREEN_W, 34), pygame.SRCALPHA)
            box.fill((0, 0, 0, 155))
            self.screen.blit(box, (0, 16))
            txt = self.font_medium.render(self.toast, True, WHITE)
            self.screen.blit(txt, (SCREEN_W // 2 - txt.get_width() // 2, 21))

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

