# backend/game_engine.py
import pygame

from utils.constants import SCREEN_H, TeamType
from utils.messages import add_message, draw_messages


class GameEngine:
    def __init__(self, game_api, renderer, ui, screen, font, clock):
        self.game_api = game_api
        self.renderer = renderer
        self.ui = ui
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
                action = self.ui.handle_event(
                    event, snapshot["units"], self.selected_id
                )
                if action:
                    result = self.ui.apply_action(action, self.game_api)
                    self.selected_id = result.get("selected_id", self.selected_id)
        return True

    def run_turns(self):
        if self.current_team == TeamType.PLAYER:
            if self.game_api.turn_check_end(self.game_api.board, TeamType.PLAYER):
                self.current_team = TeamType.AI
                self.game_api.turn_begin_reset(self.game_api.board, TeamType.AI)
                add_message("AI's turn!")
        elif self.current_team == TeamType.AI:
            self.game_api.run_ai_turn(
                self.game_api.board, self.game_api.agent, TeamType.AI
            )
            self.game_api.turn_begin_reset(self.game_api.board, TeamType.PLAYER)
            self.current_team = TeamType.PLAYER
            add_message("Player's turn!")

    def render(self):
        snapshot = self.game_api.get_board_snapshot()
        self.screen.fill((240, 240, 240))
        self.renderer.draw_grid(self.screen, snapshot)
        self.renderer.draw_units(self.screen, snapshot, self.selected_id)
        draw_messages(self.screen, self.font, SCREEN_H)
        pygame.display.flip()

    def check_winner(self):
        winner = self.game_api.get_winner(self.game_api.board)
        if winner is None:
            return False

        if winner == 0:
            winner_text = "Draw!"
        elif winner == TeamType.PLAYER:
            winner_text = "Player wins!"
        else:
            winner_text = "AI wins!"

        add_message(winner_text)
        self.renderer.draw_center_text(self.screen, winner_text)
        pygame.display.flip()
        pygame.time.delay(3000)
        return True

    def run(self):
        game_active = True
        while game_active:
            if not self.handle_player_events():
                return False  # user quit

            self.run_turns()
            self.render()

            if self.check_winner():
                game_active = False

            self.clock.tick(60)
        return True
