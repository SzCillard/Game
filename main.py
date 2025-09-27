# main.py
import pygame

from ai.basic_agent import BasicAgent
from api.api import GameAPI
from backend.board import GameState, create_default_map
from backend.logic import apply_attack, move_unit
from backend.units import Archer, Swordsman
from frontend.renderer import Renderer
from frontend.ui import UI
from utils.constants import (
    CELL_SIZE,
    EPSILON,
    GRID_H,
    GRID_W,
    SCREEN_H,
    SCREEN_W,
    TeamType,
)
from utils.logging import create_log_file, logger
from utils.messages import add_message, draw_messages


def main():
    pygame.init()
    pygame.font.init()

    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Commanders' Arena")
    font = pygame.font.Font(None, 28)

    renderer = Renderer(cell_size=CELL_SIZE, font=font)
    ui = UI(cell_size=CELL_SIZE)

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

    create_log_file()

    selected_id = None
    current_team = TeamType.PLAYER
    running = True
    add_message("Player's turn!")

    while running:
        screen.fill((240, 240, 240))
        snapshot = board_api.get_board_snapshot()

        # --- Event handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if current_team == TeamType.PLAYER:
                action = ui.handle_event(event, snapshot["units"], selected_id)
                if action:
                    result = ui.apply_action(action, board_api)
                    selected_id = result.get("selected_id", selected_id)

        # --- Check if all player units have acted ---
        if current_team == TeamType.PLAYER:
            player_units = [
                u for u in board_api.get_units() if u.team == TeamType.PLAYER
            ]
            # Mark stuck units as acted if they cannot move anymore
            for u in player_units:
                if u.move_points <= EPSILON:
                    u.has_acted = True

            if all(u.has_acted for u in player_units):
                current_team = TeamType.AI
                add_message("AI's turn!")

        # --- AI turn ---
        if current_team == TeamType.AI:
            ai_units = [
                u
                for u in board_api.get_units()
                if u.team == TeamType.AI and not u.has_acted and u.move_points > EPSILON
            ]
            for unit in ai_units:
                while unit.move_points > EPSILON and not unit.has_acted:
                    snapshot = board_api.get_board_snapshot()
                    action = board_api.agent.decide_next_action(snapshot, TeamType.AI)

                    if not action:
                        unit.has_acted = True
                        break

                    if action["type"] == "move":
                        nx, ny = action["target"]
                        if not move_unit(unit, board_api.board, nx, ny):
                            # Cannot move → end turn
                            unit.has_acted = True
                            break

                    elif action["type"] == "attack":
                        defender = next(
                            (
                                u
                                for u in board_api.get_units()
                                if u.id == action["target"]
                            ),
                            None,
                        )
                        if defender:
                            apply_attack(unit, defender, board_api.board)
                        unit.has_acted = True
                        break

            # Reset player units for next turn
            for u in board_api.get_units():
                u.move_points = u.move_range
                u.has_attacked = False
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
    logger("Exited game loop")


if __name__ == "__main__":
    main()
