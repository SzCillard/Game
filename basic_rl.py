import numpy as np
import random

# 🌍 KÖRNYEZET DEFINIÁLÁSA
grid_size = 5  # 5x5-ös mátrix
start = (0, 0)  # Kiindulópont
goal = (4, 4)   # Cél
obstacles = [(1, 1), (2, 2), (4, 1)]  # Akadályok

# 📌 Állapotok és akciók
actions = ["up", "down", "left", "right"]
q_table = np.zeros((grid_size, grid_size, len(actions)))  # Q-tábla inicializálása

# Map to print
def print_map():
    for i in range(grid_size):
        for j in range(grid_size):
            if (i, j) == start:
                print("🟢", end=" ")
            elif (i, j) == goal:
                print("🔵", end=" ")
            elif (i, j) in obstacles:
                print("⚫️", end=" ")
            else:
                print("⚪️", end=" ")
        print()

# 🎯 Jutalmazási rendszer
def get_reward(state):
    if state == goal:
        return 10  # Nagy jutalom, ha elérte a célt
    elif state in obstacles:
        return -10  # Büntetés, ha akadályba ütközik
    else:
        return -1  # Kis negatív jutalom (hogy ösztönözze a gyors mozgást)

# 🔄 Akciók végrehajtása
def take_action(state, action):
    x, y = state
    if action == "up":
        x = max(0, x - 1)
    elif action == "down":
        x = min(grid_size - 1, x + 1)
    elif action == "left":
        y = max(0, y - 1)
    elif action == "right":
        y = min(grid_size - 1, y + 1)
    return (x, y)

# 🏆 Q-learning algoritmus
alpha = 0.1  # Tanulási ráta
gamma = 0.9  # Jövőbeli jutalom fontossága
epsilon = 0.1  # Véletlenszerű felfedezés aránya

for episode in range(1000):  # 1000 tanítási epizód
    state = start
    while state != goal:
        if random.uniform(0, 1) < epsilon:
            action = random.choice(actions)  # Véletlenszerű akció (felfedezés)
        else:
            action = actions[np.argmax(q_table[state[0], state[1]])]  # Legjobb ismert akció

        new_state = take_action(state, action)
        reward = get_reward(new_state)

        # 📌 Q-tábla frissítése (Q-learning szabály)
        q_table[state[0], state[1], actions.index(action)] = (
            (1 - alpha) * q_table[state[0], state[1], actions.index(action)]
            + alpha * (reward + gamma * np.max(q_table[new_state[0], new_state[1]]))
        )

        state = new_state  # Lépjünk az új állapotba

# 📌 Kiíratjuk a tanult Q-táblát
print("Tanult Q-tábla:")
print_map()
print(q_table)
