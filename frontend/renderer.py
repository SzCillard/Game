# frontend/renderer.py
import pygame
import os

from utils.constants import (
    GRID_COLOR,
    HP_BG,
    HP_FG,
    TEAM_COLORS,
    TILE_COLORS,
    TILE_HIGHLIGHT_COLOR,
    TileHighlightType,
    UnitType,
    TeamType,
    SCREEN_W,
    SCREEN_H,
    SIDEBAR_WIDTH,
)


class Renderer:
    def __init__(self, cell_size: int, font: pygame.font.Font):
        self.cell_size = cell_size
        self.font = font
        self.unit_images = self._load_unit_images()

    def _load_unit_images(self):
        """Preload all unit images into a dict for quick access."""
        images = {}
        base_path = os.path.join("images")

        for unit in UnitType:
            images[unit] = {}
            for team in TeamType:
                team_name = "purple" if team == TeamType.PLAYER else "red"
                path = os.path.join(
                    base_path, unit.name.lower(), f"{unit.name.lower()}_{team_name}.png"
                )
                if os.path.exists(path):
                    img = pygame.image.load(path).convert_alpha()
                    img = pygame.transform.scale(img, (self.cell_size, self.cell_size))
                    images[unit][team] = img
                else:
                    print(f"⚠️ Missing image: {path}")
                    images[unit][team] = None
        return images

    # ------------------------------
    # Board
    # ------------------------------
    def draw_grid(self, screen, board_snapshot):
        tiles = board_snapshot["tiles"]
        for y, row in enumerate(tiles):
            for x, tile in enumerate(row):
                rect = pygame.Rect(
                    x * self.cell_size + SIDEBAR_WIDTH,  # shift right
                    y * self.cell_size,
                    self.cell_size,
                    self.cell_size,
                )
                pygame.draw.rect(screen, TILE_COLORS[tile], rect)
                pygame.draw.rect(screen, GRID_COLOR, rect, width=1)

    def draw_units(self, screen, board_snapshot, selected_id=None):
        units = board_snapshot["units"]

        for u in units:
            unit_type = UnitType[u["name"].upper()]
            team = TeamType(u["team"])

            rect = pygame.Rect(
                u["x"] * self.cell_size + SIDEBAR_WIDTH,  # shift right
                u["y"] * self.cell_size,
                self.cell_size,
                self.cell_size,
            )

            img = self.unit_images.get(unit_type, {}).get(team)
            if img:
                screen.blit(img, rect.topleft)
            else:
                pygame.draw.rect(
                    screen,
                    TEAM_COLORS.get(team, (100, 100, 100)),
                    rect,
                    border_radius=8,
                )

            # HP bubble
            hp_text = self.font.render(str(max(0, u["health"])), True, HP_FG)
            bubble = pygame.Rect(rect.right - 22, rect.top + 4, 18, 18)
            pygame.draw.rect(screen, HP_BG, bubble, border_radius=6)
            screen.blit(hp_text, (bubble.x + 3, bubble.y + 1))

        if selected_id is not None:
            selected = next((u for u in units if u["id"] == selected_id), None)
            if selected:
                highlight = pygame.Rect(
                    selected["x"] * self.cell_size + SIDEBAR_WIDTH,
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
        # Movement (blue outlines)
        for x, y in move_tiles:
            rect = pygame.Rect(
                x * self.cell_size + SIDEBAR_WIDTH,
                y * self.cell_size,
                self.cell_size,
                self.cell_size,
            )
            pygame.draw.rect(
                screen, TILE_HIGHLIGHT_COLOR[TileHighlightType.MOVE], rect, width=3
            )

        # Attack (semi-transparent red)
        attack_overlay = pygame.Surface(
            (self.cell_size, self.cell_size), pygame.SRCALPHA
        )
        attack_overlay.fill((*TILE_HIGHLIGHT_COLOR[TileHighlightType.ATTACK], 120))
        for x, y in attack_tiles:
            screen.blit(
                attack_overlay, (x * self.cell_size + SIDEBAR_WIDTH, y * self.cell_size)
            )

    # ------------------------------
    # Sidebar
    # ------------------------------
    def draw_sidebar(self, screen, board_snapshot, selected_id):
        sidebar_rect = pygame.Rect(0, 0, SIDEBAR_WIDTH, SCREEN_H)
        pygame.draw.rect(screen, (230, 230, 230), sidebar_rect)  # light gray bg
        pygame.draw.line(
            screen, (100, 100, 100), (SIDEBAR_WIDTH, 0), (SIDEBAR_WIDTH, SCREEN_H), 2
        )

        if selected_id is not None:
            selected = next(
                (u for u in board_snapshot["units"] if u["id"] == selected_id), None
            )
            if selected:
                y = 20
                screen.blit(
                    self.font.render(f"{selected['name']}", True, (0, 0, 0)), (20, y)
                )
                y += 30
                screen.blit(
                    self.font.render(f"HP: {selected['health']}", True, (0, 0, 0)),
                    (20, y),
                )
                y += 30
                screen.blit(
                    self.font.render(
                        f"Move points: {selected['move_points']}", True, (0, 0, 0)
                    ),
                    (20, y),
                )
                y += 30
                screen.blit(
                    self.font.render(
                        f"Attack power: {selected['attack_power']}", True, (0, 0, 0)
                    ),
                    (20, y),
                )
                y += 30
                screen.blit(
                    self.font.render(
                        f"Attack range: {selected['attack_range']}", True, (0, 0, 0)
                    ),
                    (20, y),
                )

        # Bottom menu
        menu_y = SCREEN_H - 100
        for i, text in enumerate(["[M] Menu", "[Q] Quit", "[H] Help"]):
            surf = self.font.render(text, True, (50, 50, 50))
            screen.blit(surf, (20, menu_y + i * 30))
