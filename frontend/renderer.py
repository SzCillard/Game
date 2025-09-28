# frontend/renderer.py
import pygame

from utils.constants import GRID_COLOR, HP_BG, HP_FG, TILE_COLORS


class Renderer:
    def __init__(self, cell_size: int, font: pygame.font.Font):
        self.cell_size = cell_size
        self.font = font

    def draw_grid(self, screen, board_snapshot):
        tiles = board_snapshot["tiles"]
        for y, row in enumerate(tiles):
            for x, tile in enumerate(row):
                rect = pygame.Rect(
                    x * self.cell_size,
                    y * self.cell_size,
                    self.cell_size,
                    self.cell_size,
                )
                pygame.draw.rect(screen, TILE_COLORS[tile], rect)
                pygame.draw.rect(screen, GRID_COLOR, rect, width=1)

    def draw_units(self, screen, board_snapshot, selected_id=None):
        units = board_snapshot["units"]
        from utils.constants import TEAM_COLORS

        for u in units:
            color = TEAM_COLORS.get(u["team"], (100, 100, 100))
            rect = pygame.Rect(
                u["x"] * self.cell_size,
                u["y"] * self.cell_size,
                self.cell_size,
                self.cell_size,
            )
            pygame.draw.rect(screen, color, rect, border_radius=8)

            name_surf = self.font.render(u["name"][0], True, (255, 255, 255))
            screen.blit(name_surf, (rect.x + 6, rect.y + 4))

            hp_text = self.font.render(str(max(0, u["health"])), True, HP_FG)
            bubble = pygame.Rect(rect.right - 22, rect.top + 4, 18, 18)
            pygame.draw.rect(screen, HP_BG, bubble, border_radius=6)
            screen.blit(hp_text, (bubble.x + 3, bubble.y + 1))

        if selected_id is not None:
            selected = next((u for u in units if u["id"] == selected_id), None)
            if selected:
                highlight = pygame.Rect(
                    selected["x"] * self.cell_size,
                    selected["y"] * self.cell_size,
                    self.cell_size,
                    self.cell_size,
                )
                pygame.draw.rect(
                    screen, (255, 230, 80), highlight, width=3, border_radius=8
                )

    def draw_center_text(self, screen, text):
        sw, sh = screen.get_size()
        surf = self.font.render(text, True, (10, 10, 10))
        screen.blit(
            surf, (sw // 2 - surf.get_width() // 2, sh // 2 - surf.get_height() // 2)
        )

    def draw_highlights(self, screen, move_tiles, attack_tiles):
        # Movement highlights (blue outlines)
        for x, y in move_tiles:
            rect = pygame.Rect(
                x * self.cell_size, y * self.cell_size, self.cell_size, self.cell_size
            )
            pygame.draw.rect(screen, (100, 150, 255), rect, width=3)

        # Attack highlights (red outlines)
        for x, y in attack_tiles:
            rect = pygame.Rect(
                x * self.cell_size, y * self.cell_size, self.cell_size, self.cell_size
            )
            pygame.draw.rect(screen, (255, 100, 100), rect, width=3)
