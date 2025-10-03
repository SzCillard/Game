import pygame

from utils.constants import SCREEN_H, TeamType
from utils.messages import add_message


class GameEngine:
    def __init__(self, game_api, screen, font, clock):
        self.game_api = game_api
        self.screen = screen
        self.font = font
        self.clock = clock

        self.selected_id = None
        self.current_team = TeamType.PLAYER
        add_message("Player's turn!")

    def handle_player_events(self):
        snapshot = self.game_api.get_board_snapshot()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if self.current_team == TeamType.PLAYER:
                action = self.game_api.handle_ui_event(
                    event, snapshot["units"], self.selected_id
                )
                if action:
                    result = self.game_api.apply_ui_action(action)

                    # --- Sidebar button handling ---
                    if result.get("end_turn_requested"):
                        # Force all player's units to "acted"
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

                    self.selected_id = result.get("selected_id", self.selected_id)
        return True

    def render(self):
        snapshot = self.game_api.get_board_snapshot()
        self.screen.fill((240, 240, 240))
        self.game_api.draw(self.screen, snapshot, self.selected_id)

        if self.selected_id is not None:
            unit = next(
                (u for u in self.game_api.get_units() if u.id == self.selected_id), None
            )
            if unit:
                move_tiles = self.game_api.get_movable_tiles(unit)
                attack_tiles = self.game_api.get_attackable_tiles(unit)
                self.game_api.draw_highlights(self.screen, move_tiles, attack_tiles)

        self.game_api.draw_messages(self.screen, self.font, SCREEN_H)
        pygame.display.flip()

    def check_winner(self):
        winner = self.game_api.get_winner()
        if winner is None:
            return False

        if winner == 0:
            winner_text = "Draw!"
        elif winner == TeamType.PLAYER:
            winner_text = "Player wins!"
        else:
            winner_text = "AI wins!"

        add_message(winner_text)
        self.game_api.draw_center_text(self.screen, winner_text)
        pygame.display.flip()
        pygame.time.delay(3000)
        return True

    def run_turns(self):
        if self.current_team == TeamType.PLAYER:
            if self.game_api.turn_check_end(TeamType.PLAYER):
                self.current_team = TeamType.AI
                self.game_api.turn_begin_reset(TeamType.AI)
                add_message("AI's turn!")
        elif self.current_team == TeamType.AI:
            self.game_api.run_ai_turn(TeamType.AI)
            self.game_api.turn_begin_reset(TeamType.PLAYER)
            self.current_team = TeamType.PLAYER
            add_message("Player's turn!")

    def run(self):
        game_active = True
        while game_active:
            res = self.handle_player_events()
            if res is False:
                return False
            if res == "menu":
                return "menu"

            self.run_turns()
            self.render()

            if self.check_winner():
                game_active = False

            self.clock.tick(60)
        return True
