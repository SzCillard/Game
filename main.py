# main.py
import pygame

from ai.basic_agent import BasicAgent
from api.api import GameAPI
from backend.board import GameState, create_default_map
from backend.units import Archer, Swordsman
from frontend.renderer import Renderer
from frontend.ui import UI
from utils.constants import CELL_SIZE, GRID_H, GRID_W, SCREEN_H, SCREEN_W, TeamType
from utils.messages import add_message, draw_messages


def main():
    # --- Pygame init ---
    pygame.init()
    pygame.font.init()

    # --- Screen & timing ---
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Commanders' Arena")
    font = pygame.font.Font(None, 28)

    # --- Renderer and UI ---
    renderer = Renderer(cell_size=CELL_SIZE, font=font)
    ui = UI(cell_size=CELL_SIZE)

    # --- Board & API setup ---
    game_state = GameState(
        width=GRID_W,
        height=GRID_H,
        cell_size=CELL_SIZE,
        tile_map=create_default_map(GRID_W, GRID_H),
    )

    board_api = GameAPI(
        board=game_state,
        agent=BasicAgent(),
        player_team=TeamType.PLAYER,
        ai_team=TeamType.AI,
    )

    # --- Units ---
    p1 = [
        Swordsman(1, 1, team=TeamType.PLAYER),
        Archer(2, 2, team=TeamType.PLAYER),
    ]
    p2 = [
        Swordsman(GRID_W - 2, GRID_H - 2, team=TeamType.AI),
        Archer(GRID_W - 3, GRID_H - 2, team=TeamType.AI),
    ]
    for u in p1 + p2:
        board_api.board.add_unit(u)

    # --- Game state ---
    selected_id = None
    current_team = TeamType.PLAYER
    running = True
    add_message("Player's turn!")

    # --- Main loop ---
    while running:
        # dt = clock.tick(FPS) / 1000.0
        screen.fill((240, 240, 240))

        snapshot = board_api.get_board_snapshot()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # --- Player turn ---
            if current_team == TeamType.PLAYER:
                action = ui.handle_event(event, snapshot["units"], selected_id)
                if action:
                    result = ui.apply_action(action, board_api)
                    selected_id = result.get("selected_id", selected_id)

                    # End turn if all player units have acted
                    if all(
                        u.has_acted
                        for u in board_api.get_units()
                        if u.team == TeamType.PLAYER
                    ):
                        current_team = TeamType.AI
                        add_message("AI's turn!")

        # --- AI turn ---
        if current_team == TeamType.AI:
            while True:
                action = board_api.get_ai_action()
                if not action:
                    break
                if action["type"] == "move":
                    unit = next(
                        u for u in board_api.get_units() if u.id == action["unit_id"]
                    )
                    board_api.request_move(unit, *action["target"])
                elif action["type"] == "attack":
                    attacker = next(
                        u for u in board_api.get_units() if u.id == action["unit_id"]
                    )
                    defender = next(
                        u for u in board_api.get_units() if u.id == action["target"]
                    )
                    board_api.request_attack(attacker, defender)

            # Reset player units for next turn
            for u in board_api.get_units():
                if u.team == TeamType.PLAYER:
                    u.has_acted = False
            current_team = TeamType.PLAYER
            add_message("Player's turn!")

        # --- Rendering ---
        renderer.draw_grid(screen, snapshot)
        renderer.draw_units(screen, snapshot, selected_id)
        draw_messages(screen, font, SCREEN_H)

        # --- Victory check ---
        if board_api.is_game_over():
            winner_text = board_api.get_winner()
            add_message(winner_text)
            renderer.draw_center_text(screen, winner_text)
            pygame.display.flip()
            pygame.time.delay(2000)
            running = False

        pygame.display.flip()

    pygame.quit()
    print("Exited game loop")


if __name__ == "__main__":
    main()
