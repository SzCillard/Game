# main.py
import pygame

from ai.basic_agent import BasicAgent
from api.api import GameAPI
from backend.board import GameState, create_default_map
from backend.logic import (
    check_victory,
    run_ai_turn,
    turn_begin_reset,
    turn_check_end,
)
from backend.units import Archer, Swordsman
from frontend.renderer import Renderer
from frontend.ui import UI
from utils.constants import CELL_SIZE, GRID_H, GRID_W, SCREEN_H, SCREEN_W, TeamType
from utils.logging import create_log_file, logger
from utils.messages import add_message, draw_messages


def main():
    # --- Pygame setup ---
    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Commanders' Arena")
    font = pygame.font.Font(None, 28)

    renderer = Renderer(cell_size=CELL_SIZE, font=font)
    ui = UI(cell_size=CELL_SIZE)

    create_log_file()
    clock = pygame.time.Clock()
    running = True

    while running:
        # --- Start Menu ---
        choice = ui.start_menu(screen, font)
        if choice == "quit":
            break

        # --- Initialize new game ---
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

        selected_id = None
        current_team = TeamType.PLAYER
        add_message("Player's turn!")

        # --- Game loop ---
        game_active = True
        while game_active:
            screen.fill((240, 240, 240))
            snapshot = board_api.get_board_snapshot()

            # --- Event handling (Player only) ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

                if current_team == TeamType.PLAYER:
                    action = ui.handle_event(event, snapshot["units"], selected_id)
                    if action:
                        result = ui.apply_action(action, board_api)
                        selected_id = result.get("selected_id", selected_id)

            # --- Player turn flow ---
            if current_team == TeamType.PLAYER:
                if turn_check_end(board_api.board, TeamType.PLAYER):
                    current_team = TeamType.AI
                    turn_begin_reset(board_api.board, TeamType.AI)
                    add_message("AI's turn!")

            # --- AI turn flow ---
            if current_team == TeamType.AI:
                run_ai_turn(board_api.board, board_api.agent, TeamType.AI)
                # Reset player for next turn
                turn_begin_reset(board_api.board, TeamType.PLAYER)
                current_team = TeamType.PLAYER
                add_message("Player's turn!")

            # --- Rendering ---
            renderer.draw_grid(screen, snapshot)
            renderer.draw_units(screen, snapshot, selected_id)
            draw_messages(screen, font, SCREEN_H)

            # --- Victory check ---
            winner = check_victory(board_api.board)
            if winner is not None:
                if winner == 0:
                    winner_text = "Draw!"
                elif winner == TeamType.PLAYER:
                    winner_text = "Player wins!"
                else:
                    winner_text = "AI wins!"

                add_message(winner_text)
                renderer.draw_center_text(screen, winner_text)
                pygame.display.flip()
                pygame.time.delay(2000)
                game_active = False  # exit inner game loop

            pygame.display.flip()
            clock.tick(60)

    pygame.quit()
    print("Exited game loop")
    logger("Exited game loop")


if __name__ == "__main__":
    main()
