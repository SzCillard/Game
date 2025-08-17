import math
import random

import numpy as np
import pygame

# --- Pygame inicializálás ---
pygame.init()

# --- Konstansok ---
GRID_SIZE = 20  # 20x20 pálya
TILE_SIZE = 30  # Minden mező 30 pixel
SCREEN_SIZE = GRID_SIZE * TILE_SIZE
screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
pygame.display.set_caption("Hex Kriegsspiel - MCTS AI")

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
    "archer": {
        "movement": 3,
        "attack": 2,
        "range_attack": 5,
        "armor": 1,
        "health": 5,
        "cost": 10,
    },
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
    terrain[random.randint(0, GRID_SIZE - 1)][random.randint(0, GRID_SIZE - 1)] = 1

# --- Egységek létrehozása ---
player_units = [Warrior("swordsman", 1, 1, 1), Warrior("archer", 2, 2, 1)]
ai_units = [Warrior("horseman", 18, 18, 2), Warrior("spearman", 17, 17, 2)]


# --- Monte Carlo Tree Search (MCTS) AI ---
class MCTSNode:
    def __init__(self, state, parent=None):
        self.state = state
        self.parent = parent
        self.children = []
        self.visits = 0
        self.wins = 0

    def select(self):
        """Upper Confidence Bound (UCB1) alapján kiválaszt egy gyermeket"""
        if len(self.children) == 0:
            return self
        return max(
            self.children,
            key=lambda c: c.wins / (c.visits + 1)
            + math.sqrt(2 * math.log(self.visits + 1) / (c.visits + 1)),
        )

    def expand(self):
        """Új gyermek csomópontokat generál a lehetséges lépésekhez"""
        possible_moves = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        for move in possible_moves:
            new_x = self.state[0] + move[0]
            new_y = self.state[1] + move[1]
            if 0 <= new_x < GRID_SIZE and 0 <= new_y < GRID_SIZE:
                new_state = (new_x, new_y)
                self.children.append(MCTSNode(new_state, self))

    def simulate(self):
        """Random lépésekkel szimulál egy játékot és visszatér egy eredménnyel"""
        return random.choice([0, 1])  # Nyertes vagy vesztes állapot véletlenszerűen

    def backpropagate(self, result):
        """A szimuláció eredményét visszaterjeszti a fa szintjeire"""
        self.visits += 1
        self.wins += result
        if self.parent:
            self.parent.backpropagate(result)


def mcts_search(start_state, iterations=100):
    root = MCTSNode(start_state)
    for _ in range(iterations):
        node = root.select()
        node.expand()
        selected_child = random.choice(node.children) if node.children else node
        result = selected_child.simulate()
        selected_child.backpropagate(result)
    return (
        max(root.children, key=lambda c: c.visits).state
        if root.children
        else start_state
    )


# --- Fő ciklus ---
running = True
selected_unit = None
while running:
    screen.fill(WHITE)

    # Rajzoljuk a pályát
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            color = GREEN if terrain[x, y] == 0 else BLACK
            pygame.draw.rect(
                screen, color, (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            )

    # Rajzoljuk az egységeket
    for unit in player_units + ai_units:
        color = BLUE if unit.team == 1 else RED
        pygame.draw.circle(
            screen,
            color,
            (unit.x * TILE_SIZE + TILE_SIZE // 2, unit.y * TILE_SIZE + TILE_SIZE // 2),
            TILE_SIZE // 3,
        )

    # AI mozgás MCTS alapján
    for unit in ai_units:
        new_x, new_y = mcts_search((unit.x, unit.y))
        unit.move(new_x - unit.x, new_y - unit.y)

    # Eseménykezelés
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    pygame.display.flip()

pygame.quit()
