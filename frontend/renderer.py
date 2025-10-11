# frontend/renderer.py
import os

import pygame

from utils.constants import (
    DAMAGE_DISPLAY_TIME,
    GRID_COLOR,
    SCREEN_H,
    SIDEBAR_WIDTH,
    TEAM_COLORS,
    TERRAIN_ATTACK_BONUS,
    TERRAIN_DEFENSE_BONUS,
    TILE_COLORS,
    TILE_HIGHLIGHT_COLOR,
    TeamType,
    TileHighlightType,
    UnitType,
)


class Renderer:
    """
    Handles all rendering and drawing operations for the game interface.

    This includes:
        - Board rendering (tiles, grid, highlights)
        - Unit rendering (sprites, HP bars, damage text)
        - Sidebar and UI button rendering

    The class separates drawing logic from game logic for cleaner architecture.
    """

    def __init__(self, cell_size: int, font: pygame.font.Font):
        """
        Initialize the renderer with grid and font data.

        Args:
            cell_size (int): Pixel size for each map cell.
            font (pygame.font.Font): Font used for UI text rendering.
        """
        self.cell_size = cell_size
        self.font = font
        self.unit_images = self._load_unit_images()  # Preload all unit images
        self.sidebar_buttons = {}  # Mapping of {button_label: pygame.Rect}

    # ------------------------------
    # Image Loading
    # ------------------------------

    def _load_unit_images(self):
        """
        Preload all unit images for both teams.

        Returns:
            dict: Nested dictionary of format:
                  images[UnitType][TeamType] = pygame.Surface
        """
        images = {}
        base_path = os.path.join("images")

        # Iterate over all defined unit types and team types
        for unit in UnitType:
            images[unit] = {}
            for team in TeamType:
                team_name = "purple" if team == TeamType.PLAYER else "red"
                path = os.path.join(
                    base_path, unit.name.lower(), f"{unit.name.lower()}_{team_name}.png"
                )

                # Load and scale if exists, else use None
                if os.path.exists(path):
                    img = pygame.image.load(path).convert_alpha()
                    img = pygame.transform.scale(img, (self.cell_size, self.cell_size))
                    images[unit][team] = img
                else:
                    print(f"⚠️ Missing image: {path}")
                    images[unit][team] = None
        return images

    # ------------------------------
    # Board Rendering
    # ------------------------------

    def draw_grid(self, screen, board_snapshot):
        """
        Draw the game board including terrain tiles and grid lines.

        Args:
            screen (pygame.Surface): Main display surface.
            board_snapshot (dict): Contains current board tile data.
        """
        tiles = board_snapshot["tiles"]
        for y, row in enumerate(tiles):
            for x, tile in enumerate(row):
                rect = pygame.Rect(
                    x * self.cell_size + SIDEBAR_WIDTH,  # shift right for sidebar
                    y * self.cell_size,
                    self.cell_size,
                    self.cell_size,
                )
                # Draw tile color
                pygame.draw.rect(screen, TILE_COLORS[tile], rect)
                # Draw grid outline
                pygame.draw.rect(screen, GRID_COLOR, rect, width=1)

    def draw_center_text(self, screen, text):
        """
        Draw text centered on the screen (used for 'Victory', 'Defeat', etc.)

        Args:
            screen (pygame.Surface): Display surface.
            text (str): Message to render.
        """
        sw, sh = screen.get_size()
        surf = self.font.render(text, True, (10, 10, 10))
        screen.blit(
            surf, (sw // 2 - surf.get_width() // 2, sh // 2 - surf.get_height() // 2)
        )

    def draw_highlights(self, screen, move_tiles, attack_tiles):
        """
        Highlight movement and attack ranges.

        Args:
            screen (pygame.Surface): Display surface.
            move_tiles (list[tuple]): List of (x, y) tiles in movement range.
            attack_tiles (list[tuple]): List of (x, y) tiles in attack range.
        """
        # Movement (blue outline)
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

        # Attack (semi-transparent red overlay)
        attack_overlay = pygame.Surface(
            (self.cell_size, self.cell_size), pygame.SRCALPHA
        )
        attack_overlay.fill((*TILE_HIGHLIGHT_COLOR[TileHighlightType.ATTACK], 120))
        for x, y in attack_tiles:
            screen.blit(
                attack_overlay, (x * self.cell_size + SIDEBAR_WIDTH, y * self.cell_size)
            )

    # ------------------------------
    # Unit Rendering
    # ------------------------------

    def draw_units(self, screen, board_snapshot, selected_id=None):
        """
        Draw all units, their health bars, and any floating damage text.

        Args:
            screen (pygame.Surface): Display surface.
            board_snapshot (dict): Contains 'units' and their current stats.
            selected_id (Optional[int]): Currently selected unit ID.
        """
        units = board_snapshot["units"]

        for u in units:
            unit_type = UnitType[u["name"].upper()]
            team = u["team"] if isinstance(u["team"], TeamType) else TeamType(u["team"])

            rect = pygame.Rect(
                u["x"] * self.cell_size + SIDEBAR_WIDTH,
                u["y"] * self.cell_size,
                self.cell_size,
                self.cell_size,
            )

            # Draw sprite or fallback rectangle
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

            # Draw health bar and damage text
            if "max_hp" in u:
                self._draw_health_bar(screen, u, rect)
            self._draw_damage_number(screen, u, rect)

        # Highlight the currently selected unit
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

    def _draw_health_bar(self, screen, unit: dict, rect: pygame.Rect):
        """
        Draw a small health bar above a unit.

        Args:
            screen (pygame.Surface): Display surface.
            unit (dict): Unit data (contains 'health' and 'max_hp').
            rect (pygame.Rect): Unit’s screen rectangle.
        """
        if unit["health"] <= 0:
            return

        bar_width = self.cell_size - 4
        bar_height = 6
        bar_x = rect.x + 2
        bar_y = rect.y - 8

        # Draw background
        pygame.draw.rect(screen, (60, 60, 60), (bar_x, bar_y, bar_width, bar_height))

        # Determine color by HP ratio
        ratio = unit["health"] / unit["max_hp"]
        if ratio > 0.6:
            color = (0, 200, 0)  # green
        elif ratio > 0.3:
            color = (200, 200, 0)  # yellow
        else:
            color = (200, 0, 0)  # red

        # Draw filled portion
        pygame.draw.rect(
            screen, color, (bar_x, bar_y, int(bar_width * ratio), bar_height)
        )

    def _draw_damage_number(self, screen, unit: dict, rect: pygame.Rect):
        """
        Draw floating red damage text above unit.

        Args:
            screen (pygame.Surface): Display surface.
            unit (dict): Unit data with damage info.
            rect (pygame.Rect): Unit position rect.
        """
        timer = unit.get("damage_timer", 0)
        dmg = unit.get("last_damage", 0)

        # Skip if no recent damage
        if timer <= 0 or dmg <= 0:
            return

        font = pygame.font.Font(None, 24)
        dmg_text = font.render(f"-{dmg}", True, (255, 0, 0))

        # Make text float upward over time
        total_time = DAMAGE_DISPLAY_TIME
        elapsed = total_time - timer
        offset_y = elapsed // 2

        dmg_x = rect.centerx - dmg_text.get_width() // 2
        dmg_y = rect.y - 20 - offset_y
        screen.blit(dmg_text, (dmg_x, dmg_y))

    # ------------------------------
    # Sidebar Rendering
    # ------------------------------

    def draw_sidebar(self, screen, board_snapshot, selected_id):
        """
        Render the sidebar panel with unit info and action buttons.

        Args:
            screen (pygame.Surface): Display surface.
            board_snapshot (dict): Board and unit state data.
            selected_id (Optional[int]): Currently selected unit ID.
        """
        sidebar_rect = pygame.Rect(0, 0, SIDEBAR_WIDTH, SCREEN_H)
        pygame.draw.rect(screen, (230, 230, 230), sidebar_rect)
        pygame.draw.line(
            screen, (100, 100, 100), (SIDEBAR_WIDTH, 0), (SIDEBAR_WIDTH, SCREEN_H), 2
        )

        y = 20  # Vertical cursor for text placement

        # --- Selected unit info ---
        if selected_id is not None:
            selected = next(
                (u for u in board_snapshot["units"] if u["id"] == selected_id), None
            )
            if selected:
                # Unit name
                name_surf = self.font.render(
                    f"{selected['name'].capitalize()}", True, (0, 0, 0)
                )
                screen.blit(name_surf, (20, y))
                y += 30

                # Unit stats
                stats = [
                    ("HP", selected["health"]),
                    ("Move points", selected["move_points"]),
                    ("Attack power", selected["attack_power"]),
                    ("Attack range", selected["attack_range"]),
                ]
                for label, value in stats:
                    surf = self.font.render(f"{label}: {value}", True, (0, 0, 0))
                    screen.blit(surf, (20, y))
                    y += 30

                # Terrain bonuses
                self._draw_terrain_bonus(board_snapshot, selected, screen, y)

        # --- Bottom menu buttons ---
        menu_items = ["End Turn", "Menu", "Quit", "Help"]
        btn_width, btn_height = SIDEBAR_WIDTH - 40, 40
        menu_y = SCREEN_H - (len(menu_items) * (btn_height + 10)) - 20

        mouse_x, mouse_y = pygame.mouse.get_pos()
        self.sidebar_buttons.clear()

        # Draw each button
        for i, text in enumerate(menu_items):
            btn_x = 20
            btn_y = menu_y + i * (btn_height + 10)
            rect = pygame.Rect(btn_x, btn_y, btn_width, btn_height)
            self.sidebar_buttons[text] = rect

            # Hover effect
            color = (
                (255, 230, 80)
                if rect.collidepoint(mouse_x, mouse_y)
                else (200, 200, 200)
            )
            pygame.draw.rect(screen, color, rect, border_radius=8)
            pygame.draw.rect(screen, (100, 100, 100), rect, width=2, border_radius=8)

            label = self.font.render(text, True, (20, 20, 20))
            screen.blit(
                label,
                (
                    rect.centerx - label.get_width() // 2,
                    rect.centery - label.get_height() // 2,
                ),
            )

    def _draw_terrain_bonus(self, board_snapshot, selected, screen, y):
        """
        Draw terrain bonus info for the selected unit.

        Args:
            board_snapshot (dict): Contains tile data.
            selected (dict): Selected unit data.
            screen (pygame.Surface): Display surface.
            y (int): Vertical position for rendering text.
        """
        tiles = board_snapshot["tiles"]
        ux, uy = selected["x"], selected["y"]
        if 0 <= uy < len(tiles) and 0 <= ux < len(tiles[0]):
            tile = tiles[uy][ux]
            def_bonus = TERRAIN_DEFENSE_BONUS.get(tile, 0)
            atk_bonus = TERRAIN_ATTACK_BONUS.get(tile, 0)

            tile_name = tile.name.capitalize() if hasattr(tile, "name") else str(tile)
            bonus_parts = []
            if def_bonus != 0:
                bonus_parts.append(f"{int(def_bonus * 100)}% DEF")
            if atk_bonus != 0:
                bonus_parts.append(f"{int(atk_bonus * 100)}% ATK")
            if not bonus_parts:
                bonus_parts.append("No bonus")

            bonus_text = f"{tile_name}: " + ", ".join(bonus_parts)
            terr_surf = self.font.render(bonus_text, True, (0, 0, 0))
            screen.blit(terr_surf, (20, y))

    def handle_sidebar_click(self, pos):
        """
        Check if a sidebar button was clicked.

        Args:
            pos (tuple[int, int]): Mouse click position.

        Returns:
            str | None: Button label if clicked, else None.
        """
        for label, rect in self.sidebar_buttons.items():
            if rect.collidepoint(pos):
                return label
        return None
