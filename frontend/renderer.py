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
                # filename convention: swordsman_purple.png / swordsman_red.png
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

        for u in units:
            unit_type = UnitType[u["name"].upper()]  # "Swordsman" -> UnitType.SWORDSMAN
            team = TeamType(u["team"])

            rect = pygame.Rect(
                u["x"] * self.cell_size,
                u["y"] * self.cell_size,
                self.cell_size,
                self.cell_size,
            )

            # Draw image if available, else fallback to colored rectangle
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

        # Selected highlight
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
            pygame.draw.rect(
                screen, TILE_HIGHLIGHT_COLOR[TileHighlightType.MOVE], rect, width=3
            )

        # Attack highlights (semi-transparent red overlay)
        attack_overlay = pygame.Surface(
            (self.cell_size, self.cell_size), pygame.SRCALPHA
        )
        attack_overlay.fill(
            (*TILE_HIGHLIGHT_COLOR[TileHighlightType.ATTACK], 120)
        )  # RGBA
        for x, y in attack_tiles:
            screen.blit(attack_overlay, (x * self.cell_size, y * self.cell_size))
