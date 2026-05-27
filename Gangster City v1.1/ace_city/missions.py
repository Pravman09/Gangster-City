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


CITY_1_MISSIONS = [
    Mission("Fresh Start", "Rico: You look clean. Do a delivery and keep your head down.", "Reach the Market Mile contact", (1500, 1450), 80),
    Mission("Corner Store Run", "Rico: Shops keep people alive. Step inside and stock up.", "Enter a shop or restaurant interior", (1850, 1200), 90),
    Mission("First Heat", "Rico: Trouble found us. Protect my guy near the garage.", "Defeat 3 gang attackers", (2380, 1900), 140, "Pistol"),
    Mission("Clinic Favor", "Maya: A friend is hurt. Reach the clinic and keep moving.", "Reach the Slums clinic", (2050, 5480), 150),
    Mission("Slum Cleanup", "Rico: A crew is shaking down families. Clear them out.", "Defeat 5 gang attackers", (1760, 4580), 220),
    Mission("Bank Recon", "Maya: Walk into downtown and mark the bank. No shooting.", "Reach the downtown bank", (4200, 2700), 180),
    Mission("Buy Protection", "Maya: Before the big jobs, get armor from a shop or garage.", "Buy or equip armor", (2380, 1900), 160),
    Mission("Getaway Driver", "Rico: Grab a car and lose the tail.", "Enter a car and survive for 20 seconds", (2380, 1900), 220, "Shotgun", True),
    Mission("Bank Job", "Rico: Time to make noise. Rob any bank and escape.", "Rob a bank", (2550, 1380), 420),
    Mission("Grenade Lesson", "Maya: Buy grenades. Sometimes doors need persuasion.", "Own at least one grenade", (1850, 1200), 250),
    Mission("Highway Heat", "Rico: Police are watching. Stay alive through the chase.", "Survive wanted heat for 25 seconds", (5450, 3350), 360),
    Mission("Factory Boss", "Maya: The factory crew runs the guns. End it.", "Defeat the boss wave at Steelworks", (7050, 5100), 500, "Rifle"),
    Mission("Rich Hills Score", "Rico: Hit the rich district bank and get out clean.", "Rob the Rich Hills bank", (6900, 900), 650),
    Mission("City Takeover", "Maya: Every crew knows your name. Hold the factory one last time.", "Defeat 12 attackers", (7050, 5100), 900),
    Mission("Warehouse Sweep", "Rico: The last crates are moving through the warehouses. Shut it down.", "Defeat 10 warehouse guards", (7750, 5300), 700),
    Mission("Civic Favor", "Maya: Keep one honest official alive. Reach Police HQ and make the drop.", "Reach Police HQ", (4080, 5000), 500),
    Mission("Night Run", "Rico: If you can survive the heat, the city will believe the name.", "Survive wanted heat for 30 seconds", (5450, 3350), 800),
    Mission("Downtown Lockdown", "Maya: Downtown crews are boxing us in. Break the blockade.", "Defeat 14 downtown attackers", (4200, 2700), 950),
    Mission("Mansion Raid", "Rico: The rich district boss is hiding behind gates. Kick them open.", "Defeat 10 mansion guards", (7050, 1200), 1000),
    Mission("Final Payday", "Maya: One last score. Rob a bank, then vanish into City Park.", "Rob a bank and escape to City Park", (4000, 880), 1500),
]

CITY_2_MISSIONS = [
    Mission("Arrival Tax", "Vega: City 2 does not welcome tourists. Reach the airport contact alive.", "Reach the City 2 airport contact", (1280, 1150), 900),
    Mission("Neon Ambush", "Vega: The Neon Blocks crew wants a toll. Refuse loudly.", "Defeat 8 Neon Blocks gangsters", (3820, 1500), 1300, "SMG"),
    Mission("Harbor Shipment", "Maya: A weapons shipment is moving through Old Harbor. Burn the route.", "Defeat 12 harbor gangsters", (1650, 4550), 1700),
    Mission("Cartel Toll", "Vega: Cartel Row only respects heat. Survive it.", "Survive wanted heat for 45 seconds", (4750, 4700), 1900),
    Mission("Financial Core Heist", "Rico: City 2 money sits behind thicker glass. Crack the core bank.", "Rob a City 2 bank", (6980, 1560), 2600, "Heavy Rifle"),
    Mission("Estate War", "Maya: The estates hide the bigger names. Clear the guards.", "Defeat 15 estate guards", (7050, 4480), 3000),
    Mission("Airport Lockdown", "Vega: They are cutting off your exit. Hold the airport strip.", "Defeat 18 airport attackers", (1080, 1150), 3600, "Combat Shotgun"),
    Mission("City 2 Kingpin", "Rico: Bigger city, bigger throne. Take down the kingpin army.", "Defeat 25 elite gangsters", (4700, 2850), 5000, "Rocket Launcher"),
]


class MissionSystem:
    def __init__(self, city_id=1):
        self.city_id = city_id
        self.missions = [Mission(m.title, m.dialogue, m.objective, m.marker, m.reward_money, m.unlock_weapon, m.unlock_vehicle)
                         for m in (CITY_2_MISSIONS if city_id == 2 else CITY_1_MISSIONS)]
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
            wave_counts = {
                "First Heat": 3, "Slum Cleanup": 5, "Factory Boss": 8, "City Takeover": 12,
                "Warehouse Sweep": 10, "Downtown Lockdown": 14, "Mansion Raid": 10,
                "Neon Ambush": 8, "Harbor Shipment": 12, "Estate War": 15,
                "Airport Lockdown": 18, "City 2 Kingpin": 25,
            }
            if m.title in wave_counts:
                game.spawn_mission_enemies(m.marker, wave_counts[m.title])
            if m.title == "Highway Heat":
                self.survive_timer = 25
                game.wanted.crime("mission chase")
            if m.title == "Night Run":
                self.survive_timer = 30
                game.wanted.crime("mission chase")
            if m.title == "Cartel Toll":
                self.survive_timer = 45
                game.wanted.level = max(game.wanted.level, 4)
                game.wanted.timer = 45
                game.wanted.reason = "cartel heat"
        if not m.started:
            return
        if m.title in ("Fresh Start", "Bank Recon", "Clinic Favor", "Civic Favor", "Arrival Tax"):
            m.complete = True
        elif m.title == "Corner Store Run":
            m.complete = game.state == "interior" and game.current_building and game.current_building.kind in ("store", "restaurant", "gas", "gunshop")
        elif m.title in ("First Heat", "Slum Cleanup", "Factory Boss", "City Takeover", "Warehouse Sweep", "Downtown Lockdown", "Mansion Raid", "Neon Ambush", "Harbor Shipment", "Estate War", "Airport Lockdown", "City 2 Kingpin"):
            goals = {"First Heat": 3, "Slum Cleanup": 5, "Factory Boss": 8, "City Takeover": 12,
                     "Warehouse Sweep": 10, "Downtown Lockdown": 14, "Mansion Raid": 10,
                     "Neon Ambush": 8, "Harbor Shipment": 12, "Estate War": 15,
                     "Airport Lockdown": 18, "City 2 Kingpin": 25}
            defeated = sum(1 for e in game.mission_enemies if not e.alive)
            m.progress = defeated
            m.complete = defeated >= goals[m.title]
        elif m.title == "Buy Protection":
            m.complete = player.armor > 0
        elif m.title == "Getaway Driver":
            if player.in_car:
                self.survive_timer -= dt
            m.progress = int(20 - self.survive_timer)
            m.complete = self.survive_timer <= 0
        elif m.title in ("Bank Job", "Financial Core Heist"):
            m.complete = game.last_bank_robbed
        elif m.title == "Grenade Lesson":
            m.complete = player.grenades > 0 or "Grenade" in player.weapons
        elif m.title == "Highway Heat":
            if game.wanted.level > 0:
                self.survive_timer -= dt
            m.progress = int(25 - self.survive_timer)
            m.complete = self.survive_timer <= 0
        elif m.title == "Cartel Toll":
            if game.wanted.level > 0:
                self.survive_timer -= dt
            m.progress = int(45 - self.survive_timer)
            m.complete = self.survive_timer <= 0
        elif m.title == "Night Run":
            if game.wanted.level > 0:
                self.survive_timer -= dt
            m.progress = int(30 - self.survive_timer)
            m.complete = self.survive_timer <= 0
        elif m.title == "Rich Hills Score":
            m.complete = game.last_bank_robbed and dist(player.pos, (6900, 900)) < 650
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
