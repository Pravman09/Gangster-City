import random
import pygame
from .config import SCREEN_H, SCREEN_W


class WantedSystem:
    def __init__(self):
        self.level = 0
        self.timer = 0
        self.reason = ""

    def crime(self, reason):
        self.level = min(5, max(1, self.level + 1))
        self.timer = 15.0
        self.reason = reason

    def update(self, dt):
        if self.timer > 0:
            self.timer -= dt
            if self.timer <= 0:
                self.level = 0
                self.reason = ""


class EnvironmentSystem:
    def __init__(self):
        self.time = 8.0
        self.weather = "clear"
        self.weather_timer = 18

    def update(self, dt):
        self.time = (self.time + dt * 0.035) % 24
        self.weather_timer -= dt
        if self.weather_timer <= 0:
            self.weather = random.choice(["clear", "rain", "fog", "storm"])
            self.weather_timer = random.uniform(25, 55)

    @property
    def night_alpha(self):
        if 6 <= self.time <= 18:
            return 0
        if self.time > 18:
            return min(145, int((self.time - 18) / 6 * 145))
        return min(145, int((6 - self.time) / 6 * 145))

    def draw_overlay(self, surf):
        if self.weather in ("rain", "storm"):
            for x in range(0, SCREEN_W, 34):
                pygame.draw.line(surf, (120, 150, 180), (x, 0), (x - 12, 34), 1)
        if self.weather in ("fog", "storm"):
            fog = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            fog.fill((190, 200, 205, 42 if self.weather == "fog" else 28))
            surf.blit(fog, (0, 0))
        if self.night_alpha:
            night = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            night.fill((5, 15, 35, self.night_alpha))
            surf.blit(night, (0, 0))


class AudioSystem:
    def __init__(self):
        self.enabled = False
        try:
            pygame.mixer.init()
            self.enabled = True
        except pygame.error:
            self.enabled = False

    def play(self, name):
        # Procedural placeholders keep the project asset-free for now.
        return
