from __future__ import annotations

import copy

import pygame

from utils.constants import SCREEN_H, TeamType
from utils.messages import add_message
from utils.music_utils import play_battle_music


class GameEngine:
    """
    Core controller that manages game flow, input handling,
    rendering, and turn transitions between the player and AI.

    Responsibilities:
    - Process player inputs and UI actions
    - Manage alternating turns between player and AI
    - Coordinate rendering and highlight logic
    - Check win conditions and display results
    """

    def __init__(
        self,
        game_api,
        screen: pygame.Surface,
        font: pygame.font.Font,
        clock: pygame.time.Clock,
    ) -> None:
        """
        Initialize the GameEngine.

        Args:
            game_api: The main GameAPI instance that handles unit logic and game state.
            screen: The active pygame display surface.
            font: Font used for UI and text rendering.
            clock: Pygame clock to regulate frame timing.
        """
        self.game_api = game_api
        self.screen = screen
        self.font = font
        self.clock = clock

        # --- Game state tracking ---
        self.selected_id: int | None = None
        self.current_team: TeamType = TeamType.PLAYER

    def clone(self):
        return copy.deepcopy(self)

    # ------------------------------
    # Player Input Handling
    # ------------------------------
    def handle_player_events(self) -> bool | str:
        """
        Handle and dispatch player input events for the current frame.

        Converts pygame events into UI actions, applies those via GameAPI,
        and manages sidebar actions (end turn, help, quit, etc.).

        Returns:
            bool | str:
                - False → exit the game
                - "menu" → return to main menu
                - True → continue game
        """
        snapshot = self.game_api.get_board_snapshot()

        for event in pygame.event.get():
            # Handle window close
            if event.type == pygame.QUIT:
                return False

            # Handle only when it's player's turn
            if self.current_team == TeamType.PLAYER:
                action = self.game_api.handle_ui_event(
                    event, snapshot["units"], self.selected_id
                )

                if action:
                    result = self.game_api.apply_ui_action(action)

                    # --- Sidebar buttons ---
                    if result.get("end_turn_requested"):
                        # Mark all player units as having acted
                        for u in self.game_api.get_units():
                            if u.team == TeamType.PLAYER:
                                u.has_acted = True
                        self.selected_id = None

                    if result.get("menu_requested"):
                        return "menu"

                    if result.get("quit_requested"):
                        return False

                    if result.get("help_requested"):
                        add_message("📖 Help clicked (todo: implement)")

                    # Update selected unit based on result
                    self.selected_id = result.get("selected_id", self.selected_id)

        return True

    # ------------------------------
    # Rendering
    # ------------------------------
    def render(self) -> None:
        """
        Render all visible game elements, including units, highlights, and messages.

        Handles:
        - Drawing the game board and units
        - Displaying selection highlights for movement and attacks
        - Rendering game messages and UI overlays
        """
        snapshot = self.game_api.get_board_snapshot()

        # Update any active damage animations
        self.game_api.update_damage_timers()

        # Clear the screen and redraw the board
        self.screen.fill((240, 240, 240))
        self.game_api.draw(
            self.screen,
            snapshot,
            self.selected_id,
            is_player_turn=(self.current_team == TeamType.PLAYER),
        )

        # Highlight movement and attack ranges for the selected unit
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
    # Win Condition Check
    # ------------------------------
    def check_winner(self) -> bool:
        """
        Check if the game has been won, lost, or drawn.

        Displays an end-game message if a winner is found.

        Returns:
            bool: True if the game has ended, False otherwise.
        """
        winner = self.game_api.get_winner()
        if winner is None:
            return False

        # Determine outcome text
        if winner == 0:
            winner_text = "Draw!"
        elif winner == TeamType.PLAYER:
            winner_text = "Player wins!"
        else:
            winner_text = "AI wins!"

        # Display message and wait before returning
        add_message(winner_text)
        self.game_api.draw_center_text(self.screen, winner_text)
        pygame.display.flip()
        pygame.time.delay(3000)
        return True

    # ------------------------------
    # Turn Management
    # ------------------------------
    def run_turns(self) -> None:
        """
        Handle the alternation of turns between the player and the AI.

        Checks if the player's turn has ended and transitions to the AI’s turn,
        executing its logic before returning control to the player.
        """
        # --- Player's turn ---
        if self.current_team == TeamType.PLAYER:
            if self.game_api.check_turn_end(TeamType.PLAYER):
                # Transition to AI turn
                self.current_team = TeamType.AI
                self.game_api.turn_begin_reset(TeamType.AI)

        # --- AI's turn ---
        elif self.current_team == TeamType.AI:
            self.game_api.run_ai_turn(TeamType.AI)
            self.game_api.turn_begin_reset(TeamType.PLAYER)
            self.current_team = TeamType.PLAYER

    # ------------------------------
    # Main Game Loop
    # ------------------------------
    def run(self) -> bool | str:
        """
        Run the main gameplay loop.

        Handles input, rendering, and turn logic until
        a win condition or exit event occurs.

        Returns:
            bool | str:
                - True → game finished normally
                - "menu" → player chose to open menu
                - False → player quit the game
        """

        play_battle_music()

        game_active = True

        while game_active:
            # --- Input and event handling ---
            result = self.handle_player_events()
            if result is False:
                return False
            if result == "menu":
                return "menu"

            # --- Game logic and rendering ---
            self.run_turns()
            self.render()

            # --- Win condition ---
            if self.check_winner():
                game_active = False

            # Cap frame rate
            self.clock.tick(60)

        return True
