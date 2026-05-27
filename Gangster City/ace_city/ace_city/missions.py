import pygame
from .utils import dist


class Mission:
    def __init__(self, title, dialogue, objective, marker, reward_money=0, unlock_weapon=None, unlock_vehicle=False):
        self.title = title
        self.dialogue = dialogue
        self.objective = objective
        self.marker = marker
        self.reward_money = reward_money
        self.unlock_weapon = unlock_weapon
        self.unlock_vehicle = unlock_vehicle
        self.started = False
        self.complete = False
        self.progress = 0


class MissionSystem:
    def __init__(self):
        self.missions = [
            Mission("Fresh Start", "Rico: You look clean. Do a delivery and keep your head down.",
                    "Reach the Market Mile contact", (1500, 1450), 80),
            Mission("First Heat", "Rico: Trouble found us. Protect my guy near the garage.",
                    "Defeat 3 gang attackers", (2380, 1900), 140, "Pistol"),
            Mission("Bank Recon", "Maya: Walk into downtown and mark the bank. No shooting.",
                    "Reach the downtown bank", (4200, 2700), 180),
            Mission("Getaway Driver", "Rico: Grab a car and lose the tail.",
                    "Enter a car and survive for 20 seconds", (2380, 1900), 220, "Shotgun", True),
            Mission("Factory Boss", "Maya: The factory crew runs the guns. End it.",
                    "Defeat the boss wave at Steelworks", (7050, 5100), 500, "Rifle"),
        ]
        self.index = 0
        self.message_timer = 6
        self.survive_timer = 20

    @property
    def current(self):
        if self.index < len(self.missions):
            return self.missions[self.index]
        return None

    def update(self, dt, game):
        m = self.current
        if not m:
            return
        player = game.player
        if not m.started and dist(player.pos, m.marker) < 90:
            m.started = True
            game.toast = m.dialogue
            game.toast_timer = 5
            if m.title == "First Heat":
                game.spawn_mission_enemies(m.marker, 3)
            if m.title == "Factory Boss":
                game.spawn_mission_enemies(m.marker, 8)
        if not m.started:
            return
        if m.title in ("Fresh Start", "Bank Recon"):
            m.complete = True
        elif m.title == "First Heat":
            defeated = sum(1 for e in game.mission_enemies if not e.alive)
            m.progress = defeated
            m.complete = defeated >= 3
        elif m.title == "Getaway Driver":
            if player.in_car:
                self.survive_timer -= dt
            m.progress = int(20 - self.survive_timer)
            m.complete = self.survive_timer <= 0
        elif m.title == "Factory Boss":
            defeated = sum(1 for e in game.mission_enemies if not e.alive)
            m.progress = defeated
            m.complete = defeated >= 8
        if m.complete:
            player.money += m.reward_money
            player.reputation += 1
            if m.unlock_weapon:
                player.unlock_weapon(m.unlock_weapon)
            game.toast = f"Mission complete: {m.title}  +${m.reward_money}"
            if m.unlock_weapon:
                game.toast += f"  Unlocked {m.unlock_weapon}"
            game.toast_timer = 5
            self.index += 1
            self.survive_timer = 20

    def draw_marker(self, surf, cam, font):
        m = self.current
        if not m:
            return
        x, y = int(m.marker[0] - cam[0]), int(m.marker[1] - cam[1])
        pygame.draw.circle(surf, (255, 225, 65), (x, y), 22, 3)
        pygame.draw.circle(surf, (255, 225, 65), (x, y), 5)
        label = font.render("MISSION", True, (255, 240, 120))
        surf.blit(label, (x - label.get_width() // 2, y - 42))
