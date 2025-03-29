import pygame

# --- Pygame Initialization ---
pygame.init()

# --- Constants ---
GRID_WIDTH = 10
GRID_HEIGHT = 10
CELL_SIZE = 50  # Size of a single grid cell
SCREEN_WIDTH = GRID_WIDTH * CELL_SIZE
SCREEN_HEIGHT = GRID_HEIGHT * CELL_SIZE
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Grid Strategy Game")

WHITE = (255, 255, 255)
GREEN = (0, 200, 0)
RED = (200, 0, 0)
BLUE = (0, 0, 200)
BLACK = (0, 0, 0)

font = pygame.font.Font(None, 24)  # Font for attack messages
attack_messages = []  # Stores attack messages to be displayed

# --- Helper Functions ---
def pixel_to_grid(px, py):
    """ Convert pixel coordinates to grid coordinates. """
    return px // CELL_SIZE, py // CELL_SIZE

def grid_to_pixel(x, y):
    """ Convert grid coordinates to pixel coordinates. """
    return x * CELL_SIZE, y * CELL_SIZE

# --- Unit Class ---
class Unit:
    def __init__(self, name, x, y, team):
        self.name = name
        self.x = x  # Grid coordinate
        self.y = y
        self.team = team  # 1 = Player, 2 = AI
        self.health = 10  # Default health
        self.attack_power = 3
        self.move_range = 2  # Number of cells it can move

    def move(self, new_x, new_y):
        """ Move unit to a new grid location if within move range. """
        if abs(self.x - new_x) + abs(self.y - new_y) <= self.move_range:
            self.x, self.y = new_x, new_y

    def attack(self, target):
        """ Attack another unit, reducing its health. """
        target.health -= self.attack_power
        attack_messages.append(f"{self.name} attacked {target.name}! {target.name} HP: {target.health}")
        if target.health <= 0:
            attack_messages.append(f"{target.name} was defeated!")
            return True  # Target is defeated
        return False

    def draw(self, screen):
        """ Draw unit on screen. """
        px, py = grid_to_pixel(self.x, self.y)
        color = BLUE if self.team == 1 else RED
        pygame.draw.circle(screen, color, (px + CELL_SIZE // 2, py + CELL_SIZE // 2), CELL_SIZE // 3)

        # Display unit health
        health_text = font.render(str(self.health), True, BLACK)
        screen.blit(health_text, (px + CELL_SIZE // 2 - 8, py + CELL_SIZE // 2 - 25))

# --- AI Class ---
class AI:
    def take_turn(self, units):
        """ AI moves towards the nearest player unit and attacks if possible. """
        ai_units = [unit for unit in units if unit.team == 2]
        player_units = [unit for unit in units if unit.team == 1]

        for unit in ai_units:
            if player_units:
                # Find the closest player unit
                target = min(player_units, key=lambda p: abs(p.x - unit.x) + abs(p.y - unit.y))

                # Determine movement direction
                dx, dy = 0, 0
                if unit.x < target.x:
                    dx = 1
                elif unit.x > target.x:
                    dx = -1
                if unit.y < target.y:
                    dy = 1
                elif unit.y > target.y:
                    dy = -1

                # Move towards the target
                if abs(unit.x - target.x) + abs(unit.y - target.y) > 1:
                    unit.move(unit.x + dx, unit.y + dy)
                else:
                    # Attack if adjacent
                    if unit.attack(target):
                        units.remove(target)  # Remove defeated player unit

# --- Game Board ---
class GridBoard:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.units = []  # List of units
    
    def add_unit(self, unit):
        """ Add a unit to the board. """
        self.units.append(unit)

    def get_unit_at(self, x, y):
        """ Return the unit at given grid coordinates, or None. """
        for unit in self.units:
            if unit.x == x and unit.y == y:
                return unit
        return None

    def draw(self, screen):
        """ Draw the grid and units. """
        screen.fill(WHITE)
        
        # Draw the grid
        for x in range(self.width):
            for y in range(self.height):
                px, py = grid_to_pixel(x, y)
                pygame.draw.rect(screen, GREEN, (px, py, CELL_SIZE, CELL_SIZE), 2)

        # Draw the units
        for unit in self.units:
            unit.draw(screen)

# --- Game Initialization ---
board = GridBoard(GRID_WIDTH, GRID_HEIGHT)
player_unit = Unit("Swordsman", 2, 2, team=1)
ai_unit = Unit("Spearman", 7, 7, team=2)
board.add_unit(player_unit)
board.add_unit(ai_unit)
enemy_bot = AI()

# --- Game Loop ---
running = True
selected_unit = None
player_turn = True
message_timer = 0

while running:
    screen.fill(WHITE)
    board.draw(screen)

    # Display attack messages
    if attack_messages:
        message_surface = font.render(attack_messages[0], True, BLACK)
        screen.blit(message_surface, (10, SCREEN_HEIGHT - 30))
        message_timer += 1
        if message_timer > 60:  # Message disappears after 60 frames (~2 seconds)
            attack_messages.pop(0)
            message_timer = 0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and player_turn:
            px, py = pygame.mouse.get_pos()
            x, y = pixel_to_grid(px, py)

            unit = board.get_unit_at(x, y)
            if unit and unit.team == 1:  # Player selects a unit
                selected_unit = unit
            elif selected_unit and not unit:  # Move selected unit
                selected_unit.move(x, y)
                selected_unit = None
                player_turn = False
            elif selected_unit and unit and unit.team == 2:  # Attack
                if selected_unit.attack(unit):
                    board.units.remove(unit)  # Remove unit if defeated
                selected_unit = None
                player_turn = False

    if not player_turn:
        pygame.time.delay(500)  # AI reaction delay
        enemy_bot.take_turn(board.units)
        player_turn = True

    pygame.display.flip()

pygame.quit()
