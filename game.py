import pygame
import random
import numpy as np
import gymnasium as gym
from stable_baselines3 import PPO

# --- Pygame inicializálás ---
pygame.init()

# --- Konstansok ---
GRID_SIZE = 20  # 20x20 pálya
TILE_SIZE = 30  # Minden mező 30 pixel
SCREEN_SIZE = GRID_SIZE * TILE_SIZE
screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
pygame.display.set_caption("Hex Kriegsspiel RL")

# --- Színek ---
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)

# --- Egységek statjai ---
UNIT_STATS = {
    "swordsman": {"movement": 2, "attack": 4, "armor": 3, "health": 12, "cost": 14},
    "horseman": {"movement": 4, "attack": 8, "armor": 2, "health": 8, "cost": 20},
    "spearman": {"movement": 2, "attack": 5, "armor": 2, "health": 8, "cost": 12},
    "archer": {"movement": 3, "attack": 2, "range_attack": 5, "armor": 1, "health": 5, "cost": 10},
}

# --- Egység osztály ---
class Warrior:
    def __init__(self, name, x, y, team):
        self.name = name
        self.stats = UNIT_STATS[name]
        self.x = x
        self.y = y
        self.health = self.stats["health"]
        self.team = team  # 1 = játékos, 2 = AI

    def move(self, dx, dy):
        new_x, new_y = self.x + dx, self.y + dy
        if 0 <= new_x < GRID_SIZE and 0 <= new_y < GRID_SIZE:  # Maradjon a pályán
            self.x, self.y = new_x, new_y

    def attack(self, target):
        damage = abs(random.randint(0, target.stats["armor"]) - self.stats["attack"])
        target.health -= damage
        if target.health <= 0:
            return True  # Az ellenfél meghalt
        return False

# --- Pálya generálása ---
terrain = np.zeros((GRID_SIZE, GRID_SIZE))
for _ in range(30):  # Hozzáadunk akadályokat (pl. hegyek)
    terrain[random.randint(0, GRID_SIZE-1)][random.randint(0, GRID_SIZE-1)] = 1

# --- Egységek létrehozása ---
player_units = [Warrior("swordsman", 1, 1, 1), Warrior("archer", 2, 2, 1)]
ai_units = [Warrior("horseman", 18, 18, 2), Warrior("spearman", 17, 17, 2)]

# --- AI KÖRNYEZET RL-HEZ ---
class HexWarEnv(gym.Env):
    def __init__(self):
        super(HexWarEnv, self).__init__()
        self.observation_space = gym.spaces.Box(low=0, high=GRID_SIZE, shape=(2,), dtype=np.int32)
        self.action_space = gym.spaces.Discrete(4)
        self.state = np.array([18, 18])  # AI kezdeti pozíciója

    def step(self, action):
        x, y = self.state
        if action == 0: y -= 1  # Balra
        elif action == 1: y += 1  # Jobbra
        elif action == 2: x -= 1  # Fel
        elif action == 3: x += 1  # Le

        x = max(0, min(GRID_SIZE-1, x))
        y = max(0, min(GRID_SIZE-1, y))
        self.state = np.array([x, y])

        reward = -1  # Büntetés mozgásért
        done = (x, y) == (1, 1)  # Ha elérte a játékost
        if done:
            reward = 100

        return self.state, reward, done, False, {}

    def reset(self, seed=None, options=None):
        self.state = np.array([18, 18])
        return self.state, {}

# --- AI Tréning ---
env = HexWarEnv()
model = PPO("MlpPolicy", env, verbose=1)
model.learn(total_timesteps=5000)

# --- Fő ciklus ---
running = True
selected_unit = None
while running:
    screen.fill(WHITE)

    # Rajzoljuk a pályát
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            color = GREEN if terrain[x, y] == 0 else BLACK
            pygame.draw.rect(screen, color, (x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE))

    # Rajzoljuk az egységeket
    for unit in player_units + ai_units:
        color = BLUE if unit.team == 1 else RED
        pygame.draw.circle(screen, color, (unit.x*TILE_SIZE + TILE_SIZE//2, unit.y*TILE_SIZE + TILE_SIZE//2), TILE_SIZE//3)

    # AI mozgás RL alapján
    for unit in ai_units:
        state = np.array([unit.x, unit.y])
        action, _ = model.predict(state)
        if action == 0: unit.move(0, -1)
        elif action == 1: unit.move(0, 1)
        elif action == 2: unit.move(-1, 0)
        elif action == 3: unit.move(1, 0)

    # Eseménykezelés
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            x, y = pygame.mouse.get_pos()
            for unit in player_units:
                if unit.x * TILE_SIZE < x < (unit.x + 1) * TILE_SIZE and unit.y * TILE_SIZE < y < (unit.y + 1) * TILE_SIZE:
                    selected_unit = unit
        elif event.type == pygame.KEYDOWN:
            if selected_unit:
                if event.key == pygame.K_LEFT: selected_unit.move(-1, 0)
                elif event.key == pygame.K_RIGHT: selected_unit.move(1, 0)
                elif event.key == pygame.K_UP: selected_unit.move(0, -1)
                elif event.key == pygame.K_DOWN: selected_unit.move(0, 1)

    pygame.display.flip()

pygame.quit()
