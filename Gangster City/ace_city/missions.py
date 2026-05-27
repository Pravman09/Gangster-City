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
            Mission("Corner Store Run", "Rico: Shops keep people alive. Step inside and stock up.",
                    "Enter a shop or restaurant interior", (1850, 1200), 90),
            Mission("First Heat", "Rico: Trouble found us. Protect my guy near the garage.",
                    "Defeat 3 gang attackers", (2380, 1900), 140, "Pistol"),
            Mission("Clinic Favor", "Maya: A friend is hurt. Reach the clinic and keep moving.",
                    "Reach the Slums clinic", (2050, 5480), 150),
            Mission("Slum Cleanup", "Rico: A crew is shaking down families. Clear them out.",
                    "Defeat 5 gang attackers", (1760, 4580), 220),
            Mission("Bank Recon", "Maya: Walk into downtown and mark the bank. No shooting.",
                    "Reach the downtown bank", (4200, 2700), 180),
            Mission("Buy Protection", "Maya: Before the big jobs, get armor from a shop or garage.",
                    "Buy or equip armor", (2380, 1900), 160),
            Mission("Getaway Driver", "Rico: Grab a car and lose the tail.",
                    "Enter a car and survive for 20 seconds", (2380, 1900), 220, "Shotgun", True),
            Mission("Bank Job", "Rico: Time to make noise. Rob any bank and escape.",
                    "Rob a bank", (2550, 1380), 420),
            Mission("Grenade Lesson", "Maya: Buy grenades. Sometimes doors need persuasion.",
                    "Own at least one grenade", (1850, 1200), 250),
            Mission("Highway Heat", "Rico: Police are watching. Stay alive through the chase.",
                    "Survive wanted heat for 25 seconds", (5450, 3350), 360),
            Mission("Factory Boss", "Maya: The factory crew runs the guns. End it.",
                    "Defeat the boss wave at Steelworks", (7050, 5100), 500, "Rifle"),
            Mission("Rich Hills Score", "Rico: Hit the rich district bank and get out clean.",
                    "Rob the Rich Hills bank", (6900, 900), 650),
            Mission("City Takeover", "Maya: Every crew knows your name. Hold the factory one last time.",
                    "Defeat 12 attackers", (7050, 5100), 900),
            Mission("Warehouse Sweep", "Rico: The last crates are moving through the warehouses. Shut it down.",
                    "Defeat 10 warehouse guards", (7750, 5300), 700),
            Mission("Civic Favor", "Maya: Keep one honest official alive. Reach Police HQ and make the drop.",
                    "Reach Police HQ", (4080, 5000), 500),
            Mission("Night Run", "Rico: If you can survive the heat, the city will believe the name.",
                    "Survive wanted heat for 30 seconds", (5450, 3350), 800),
            Mission("Downtown Lockdown", "Maya: Downtown crews are boxing us in. Break the blockade.",
                    "Defeat 14 downtown attackers", (4200, 2700), 950),
            Mission("Mansion Raid", "Rico: The rich district boss is hiding behind gates. Kick them open.",
                    "Defeat 10 mansion guards", (7050, 1200), 1000),
            Mission("Final Payday", "Maya: One last score. Rob a bank, then vanish into City Park.",
                    "Rob a bank and escape to City Park", (4000, 880), 1500),
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
            if m.title == "Slum Cleanup":
                game.spawn_mission_enemies(m.marker, 5)
            if m.title == "Factory Boss":
                game.spawn_mission_enemies(m.marker, 8)
            if m.title == "City Takeover":
                game.spawn_mission_enemies(m.marker, 12)
            if m.title == "Warehouse Sweep":
                game.spawn_mission_enemies(m.marker, 10)
            if m.title == "Downtown Lockdown":
                game.spawn_mission_enemies(m.marker, 14)
            if m.title == "Mansion Raid":
                game.spawn_mission_enemies(m.marker, 10)
            if m.title == "Highway Heat":
                self.survive_timer = 25
                game.wanted.crime("mission chase")
            if m.title == "Night Run":
                self.survive_timer = 30
                game.wanted.crime("mission chase")
        if not m.started:
            return
        if m.title in ("Fresh Start", "Bank Recon", "Clinic Favor", "Civic Favor"):
            m.complete = True
        elif m.title == "Corner Store Run":
            m.complete = game.state == "interior" and game.current_building and game.current_building.kind in ("store", "restaurant", "gas", "gunshop")
        elif m.title == "First Heat":
            defeated = sum(1 for e in game.mission_enemies if not e.alive)
            m.progress = defeated
            m.complete = defeated >= 3
        elif m.title == "Slum Cleanup":
            defeated = sum(1 for e in game.mission_enemies if not e.alive)
            m.progress = defeated
            m.complete = defeated >= 5
        elif m.title == "Buy Protection":
            m.complete = player.armor > 0
        elif m.title == "Getaway Driver":
            if player.in_car:
                self.survive_timer -= dt
            m.progress = int(20 - self.survive_timer)
            m.complete = self.survive_timer <= 0
        elif m.title == "Bank Job":
            m.complete = game.last_bank_robbed
        elif m.title == "Grenade Lesson":
            m.complete = player.grenades > 0
        elif m.title == "Highway Heat":
            if game.wanted.level > 0:
                self.survive_timer -= dt
            m.progress = int(25 - self.survive_timer)
            m.complete = self.survive_timer <= 0
        elif m.title == "Factory Boss":
            defeated = sum(1 for e in game.mission_enemies if not e.alive)
            m.progress = defeated
            m.complete = defeated >= 8
        elif m.title == "Rich Hills Score":
            m.complete = game.last_bank_robbed and dist(player.pos, (6900, 900)) < 650
        elif m.title == "City Takeover":
            defeated = sum(1 for e in game.mission_enemies if not e.alive)
            m.progress = defeated
            m.complete = defeated >= 12
        elif m.title == "Warehouse Sweep":
            defeated = sum(1 for e in game.mission_enemies if not e.alive)
            m.progress = defeated
            m.complete = defeated >= 10
        elif m.title == "Night Run":
            if game.wanted.level > 0:
                self.survive_timer -= dt
            m.progress = int(30 - self.survive_timer)
            m.complete = self.survive_timer <= 0
        elif m.title == "Downtown Lockdown":
            defeated = sum(1 for e in game.mission_enemies if not e.alive)
            m.progress = defeated
            m.complete = defeated >= 14
        elif m.title == "Mansion Raid":
            defeated = sum(1 for e in game.mission_enemies if not e.alive)
            m.progress = defeated
            m.complete = defeated >= 10
        elif m.title == "Final Payday":
            m.complete = game.last_bank_robbed and dist(player.pos, (4000, 880)) < 650
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
            self.survive_timer = 25
            game.last_bank_robbed = False
            game.save_game()

    def draw_marker(self, surf, cam, font):
        m = self.current
        if not m:
            return
        x, y = int(m.marker[0] - cam[0]), int(m.marker[1] - cam[1])
        pygame.draw.circle(surf, (255, 225, 65), (x, y), 22, 3)
        pygame.draw.circle(surf, (255, 225, 65), (x, y), 5)
        label = font.render("MISSION", True, (255, 240, 120))
        surf.blit(label, (x - label.get_width() // 2, y - 42))


