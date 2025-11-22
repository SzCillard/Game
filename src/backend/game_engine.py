# backend/game_engine.py
from __future__ import annotations

import copy

import pygame

from utils.constants import SCREEN_H, TeamType
from utils.messages import add_message
from utils.music_utils import play_battle_music


class GameEngine:
    """
    Manages full game flow, input handling, rendering, and turn alternation.
    Supports Human vs AI and AI vs AI (self-play) modes.
    """

    def __init__(self, game_api, screen, font, clock) -> None:
        self.game_api = game_api
        self.screen = screen
        self.font = font
        self.clock = clock

        # Instead of assuming HUMAN → AI, we track team 1 and 2 generically
        self.current_team_id: int = 1
        self.selected_id: int | None = None

    def clone(self):
        return copy.deepcopy(self)

    # ------------------------------
    # Input Handling
    # ------------------------------
    def handle_human_input(self, team_id: int) -> bool | str:
        """
        Handle human player's pygame input events for this turn.
        Returns False to quit, 'menu' for menu, or True to continue.
        """
        snapshot = self.game_api.get_board_snapshot()

        for event in pygame.event.get():
            # Handle window close
            if event.type == pygame.QUIT:
                return False

            action = self.game_api.handle_ui_event(
                event, snapshot["units"], self.selected_id
            )

            if action:
                result = self.game_api.apply_ui_action(action)

                if result.get("end_turn_requested"):
                    # Mark all units for this team as done
                    for u in self.game_api.get_units():
                        if u.team_id == team_id:
                            u.has_acted = True
                    self.selected_id = None

                if result.get("menu_requested"):
                    return "menu"

                if result.get("quit_requested"):
                    return False

                if result.get("help_requested"):
                    add_message("📖 Help clicked (todo: implement)")

                self.selected_id = result.get("selected_id", self.selected_id)

        return True

    # ------------------------------
    # Rendering
    # ------------------------------
    def render(self) -> None:
        """Redraws the entire game screen and highlights."""
        snapshot = self.game_api.get_board_snapshot()
        self.game_api.update_damage_timers()

        self.screen.fill((240, 240, 240))
        self.game_api.draw(
            self.screen,
            snapshot,
            self.selected_id,
            is_player_turn=(
                self.current_team_id == 1 and self.game_api.team1_type == TeamType.HUMAN
            )
            or (
                self.current_team_id == 2 and self.game_api.team2_type == TeamType.HUMAN
            ),
        )

        if self.selected_id is not None:
            unit = next(
                (u for u in self.game_api.get_units() if u.id == self.selected_id), None
            )
            if unit:
                move_tiles = self.game_api.get_movable_tiles(unit)
                attack_tiles = self.game_api.get_attackable_tiles(unit)
                self.game_api.draw_highlights(self.screen, move_tiles, attack_tiles)

        # Display floating messages and update screen
        self.game_api.draw_messages(self.screen, self.font, SCREEN_H)
        pygame.display.flip()

    # ------------------------------
    # Turn Management
    # ------------------------------
    def run_turn(self) -> bool | str:
        """
        Execute one full turn for the current team.
        Returns False to quit, "menu" for menu, or True to continue.
        """
        current_team_id = self.current_team_id
        team_type = (
            self.game_api.team1_type
            if current_team_id == 1
            else self.game_api.team2_type
        )

        # --- Human Turn ---
        if team_type == TeamType.HUMAN:
            result = self.handle_human_input(current_team_id)
            if result is not True:
                return result

            if self.game_api.check_turn_end(current_team_id):
                self.current_team_id = 2 if current_team_id == 1 else 1
                self.game_api.start_turn(self.current_team_id)

        # --- AI Turn ---
        elif team_type == TeamType.AI:
            self.game_api.run_ai_turn(current_team_id)
            if self.game_api.check_turn_end(current_team_id):
                self.current_team_id = 2 if current_team_id == 1 else 1
                self.game_api.start_turn(self.current_team_id)

        return True

    # ------------------------------
    # Win Condition
    # ------------------------------
    def check_winner(self) -> bool:
        winner = self.game_api.get_winner()
        if winner is None:
            return False

        if winner == 0:
            text = "Draw!"
        else:
            # Check which type won (human/ai)
            if (winner == 1 and self.game_api.team1_type == TeamType.HUMAN) or (
                winner == 2 and self.game_api.team2_type == TeamType.HUMAN
            ):
                text = "Player wins!"
            else:
                text = "AI wins!"

        add_message(text)
        self.game_api.draw_center_text(self.screen, text)
        pygame.display.flip()
        pygame.time.delay(2000)
        return True

    # ------------------------------
    # Main Game Loop
    # ------------------------------
    def run(self) -> bool | str:
        """Main gameplay loop supporting AI vs AI or Human vs AI."""
        play_battle_music()
        self.game_api.start_turn(self.current_team_id)
        game_active = True

        while game_active:
            result = self.run_turn()
            if result is False:
                return False
            if result == "menu":
                return "menu"

            self.render()

            if self.check_winner():
                game_active = False

            self.clock.tick(60)

        return True
