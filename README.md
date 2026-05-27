# Gangster-City
Gangster City

**Gangster City** is a top-down open-world crime game built with **Python** and **Pygame**.  
Explore a large living city, complete story missions, drive vehicles, enter buildings, buy weapons, rob banks, survive police heat, and build your reputation across different districts.

## About The Game

Gangster City is a prototype open-world city game inspired by classic top-down action games. The player starts with very little and works through a chain of missions involving deliveries, gang fights, bank robberies, police chases, weapon unlocks, and city takeover objectives.

The game includes a large generated city map with different districts, traffic, civilians, police, enemies, shops, interiors, weather, a day-night cycle, save/load support, and a full-screen map.

## Features

- Large open-world city map
- Multiple city districts
- Story mission system
- Full mission log with completed/active/locked status
- Full-screen city map with service icons
- Minimap during gameplay
- Walking and driving controls
- Drivable vehicles
- Traffic vehicles
- Police wanted system
- Bank robbery system with police response
- Shops, gun shops, garages, banks, and hospitals
- Building interiors
- Weapons and grenades
- Civilian, enemy, and police NPCs
- Weather system: clear, rain, fog, storm
- Day-night cycle
- Save/load progress
- Autosave
- Fullscreen toggle

## City Districts

Gangster City contains several districts, each with its own atmosphere and building types:

- **Downtown** - offices, apartments, banks
- **Market Mile** - shops, gas stations, restaurants, gun shop
- **Slums** - garages, clinics, smaller shops
- **Rich Hills** - villas, mansion, rich district bank
- **Industrial** - factories, warehouses, steelworks
- **Civic Center** - police HQ, hospital, banks
- **Green Park** - park and landmark area
- **Outskirts** - mixed open city areas

## Gameplay

You can explore the city on foot or in vehicles. Missions guide you through the story, but the city also supports free-roam gameplay.

You can:

- Enter and exit cars
- Buy weapons and armor
- Visit hospitals and garages
- Enter buildings
- Rob banks
- Fight gangs
- Escape police
- Complete story missions
- Track missions from the mission log
- Use the map to find services and objectives

## Controls

| Key / Input | Action |
|---|---|
| `WASD` | Move / drive |
| Mouse click | Shoot |
| `E` | Interact / enter or exit car |
| `Z` | Enter nearest building / exit interior |
| `M` | Open map while playing / mission log from menu |
| `H` | Use hospital if nearby |
| `G` | Use garage if nearby |
| `B` | Use bank if nearby |
| `1-5` | Switch weapons |
| `F` | Toggle fullscreen |
| `Esc` | Return to menu / exit screens |
| `R` | Restart after death |

In shops and interiors:

| Key | Action |
|---|---|
| `W/S` or Arrow keys | Select item |
| `Enter`, `Space`, or `E` | Buy/use item |
| `Esc` or `Z` | Exit |

## Weapons

The game currently includes:

- Hands / no weapon
- Pistol
- Shotgun
- Rifle
- Grenades

Each weapon has different damage, fire rate, spread, and behavior.

## Missions

Gangster City includes a story mission chain with objectives such as:

- Reaching contacts
- Entering shops
- Defeating gang attackers
- Visiting clinics
- Buying armor
- Driving getaway vehicles
- Robbing banks
- Surviving police heat
- Fighting boss waves
- Taking over dangerous areas

The mission log shows which missions are complete, active, or locked.

## Bank Robbery System

Banks can be robbed from inside their interiors. Robbing a bank now triggers a harder response:

- Larger cash payout
- Immediate police alarm
- Wanted level increase
- Police officers spawn nearby
- Police cars arrive around the bank
- Player must survive the response

## Save System

The game saves progress to:

```text
gangster_city_save.json
Saved data includes:

Player position
Health and armor
Money
Weapons
Grenades
Reputation
Current mission
Kill/civilian stats
Weather and time
Requirements
Python 3
Pygame
Install Pygame with:

pip install pygame
How To Run
From the game folder, run:

python gangster_city.py
Or on Windows, double-click:

Project Structure
Gangster City/
├── gangster_city.py
├── gangster_city_save.json
└── ace_city/
    ├── game.py
    ├── entities.py
    ├── missions.py
    ├── world.py
    ├── systems.py
    ├── sprites.py
    ├── particles.py
    ├── utils.py
    └── config.py
Main Files
File	Purpose
gangster_city.py	Main launcher
game.py	Game loop, UI, save/load, combat, map, interiors
entities.py	Player, vehicles, police, enemies, civilians, bullets, grenades
missions.py	Story mission system
world.py	City generation, districts, roads, buildings
systems.py	Wanted system, weather, day-night cycle
sprites.py	Drawing characters, buildings, scenery
particles.py	Damage numbers and effects
utils.py	Collision and math helpers
config.py	Screen size, map size, colors, speed settings
Current Status
Gangster City is an in-progress prototype. It already features a playable open-world loop, missions, combat, vehicles, interiors, and saving, but there is still plenty of room for expansion.

Possible future additions:

More endgame missions
Stronger police chase AI
Police roadblocks
Gang territory control
Boss enemies
Ammo and reload system
More vehicles
Safehouses
Better audio
Improved menus and settings
More animations and visual effects

Credits
Created by Pranav 
as a Python/Pygame open-world game project.



