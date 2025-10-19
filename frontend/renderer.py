# frontend/renderer.py

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
    Color,
    TeamType,
    TileHighlightType,
    UnitType,
)
from utils.fonts import FontManager
from utils.helpers import load_unit_images


class Renderer:
    """
    Handles all rendering and drawing operations for the game interface.

    This includes:
        - Board rendering (tiles, grid, highlights)
        - Unit rendering (sprites, HP bars, damage text)
        - Sidebar and UI button rendering

    The class separates drawing logic from game logic for cleaner architecture.
    """

    def __init__(self, cell_size: int):
        """
        Initialize the renderer with grid and font data.

        Args:
            cell_size (int): Pixel size for each map cell.
            font (pygame.font.Font): Font used for UI text rendering.
        """
        self.cell_size = cell_size
        self.unit_images = load_unit_images(cell_size=cell_size)
        self.sidebar_buttons = {}  # Mapping of {button_label: pygame.Rect}
        self.fonts = FontManager()

    # ------------------------------
    # Start Menu
    # ------------------------------

    def draw_start_menu(
        self, screen: pygame.Surface, selected_index: int, options: list[str]
    ) -> None:
        """Render the main menu screen."""
        screen.fill(Color.BLACK.value)
        sw, sh = screen.get_size()

        # --- Draw title ---
        font, color = self.fonts.get("title")
        title_surf = font.render("Commanders' Arena", True, color=color)
        screen.blit(title_surf, (sw // 2 - title_surf.get_width() // 2, sh // 4 - 60))

        # --- Draw buttons ---
        mouse_x, mouse_y = pygame.mouse.get_pos()
        for i, option in enumerate(options):
            btn_width, btn_height = 220, 50
            btn_x = sw // 2 - btn_width // 2
            btn_y = sh // 2 - 40 + i * 80
            btn_rect = pygame.Rect(btn_x, btn_y, btn_width, btn_height)

            # Hover and selection
            if btn_rect.collidepoint(mouse_x, mouse_y):
                color = (255, 230, 80)
            elif i == selected_index:
                color = (255, 255, 150)
            else:
                color = (200, 200, 200)

            pygame.draw.rect(screen, color, btn_rect, border_radius=12)
            font, color = self.fonts.get("menu")
            text_surf = font.render(option, True, color=color)
            screen.blit(
                text_surf,
                (
                    btn_x + btn_width // 2 - text_surf.get_width() // 2,
                    btn_y + btn_height // 2 - text_surf.get_height() // 2,
                ),
            )

    # ------------------------------
    # Draft Menu
    # ------------------------------

    def draw_draft_screen(
        self, screen, available_units, selected_units, funds_left
    ) -> None:
        """Draw the pre-battle draft/army selection screen."""
        screen.fill((25, 25, 25))
        sw, sh = screen.get_size()
        font_title, color_title = self.fonts.get("title")
        font_text, color_text = self.fonts.get("sidebar")

        # Title
        title = font_title.render("Select Your Army", True, color_title)
        screen.blit(title, (sw // 2 - title.get_width() // 2, 40))

        # Funds display
        funds_text = font_text.render(
            f"Funds left: {funds_left}", True, (255, 255, 150)
        )
        screen.blit(funds_text, (sw // 2 - funds_text.get_width() // 2, 100))

        # Unit List
        start_y = 180
        btn_w, btn_h = 80, 35
        self.sidebar_buttons.clear()  # reuse this dict to track buttons

        for i, (name, data) in enumerate(available_units.items()):
            y = start_y + i * 70

            # Draw unit info
            info_text = f"{name} (Cost: {data['cost']})"
            surf = font_text.render(info_text, True, (220, 220, 220))
            screen.blit(surf, (150, y))

            # Add button
            add_rect = pygame.Rect(sw - 260, y, btn_w, btn_h)
            rem_rect = pygame.Rect(sw - 160, y, btn_w, btn_h)
            pygame.draw.rect(screen, (70, 200, 70), add_rect, border_radius=8)
            pygame.draw.rect(screen, (200, 70, 70), rem_rect, border_radius=8)
            self.sidebar_buttons[f"add_{name}"] = add_rect
            self.sidebar_buttons[f"rem_{name}"] = rem_rect

            add_label = font_text.render("+", True, (255, 255, 255))
            rem_label = font_text.render("-", True, (255, 255, 255))
            screen.blit(add_label, (add_rect.centerx - 5, add_rect.centery - 10))
            screen.blit(rem_label, (rem_rect.centerx - 5, rem_rect.centery - 10))

        # Player's selected army
        screen.blit(
            font_text.render("Your Army:", True, (255, 255, 255)), (150, sh - 180)
        )
        y = sh - 150
        for unit in selected_units:
            unit_text = font_text.render(unit, True, (200, 200, 200))
            screen.blit(unit_text, (180, y))
            y += 30

        # Start battle button
        start_rect = pygame.Rect(sw // 2 - 100, sh - 70, 200, 50)
        pygame.draw.rect(screen, (255, 230, 80), start_rect, border_radius=12)
        label = font_text.render("Start Battle", True, (0, 0, 0))
        screen.blit(
            label,
            (
                start_rect.centerx - label.get_width() // 2,
                start_rect.centery - label.get_height() // 2,
            ),
        )
        self.sidebar_buttons["start_battle"] = start_rect

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
        font, color = self.fonts.get("title")
        surf = font.render(text, True, color=color)
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
        Ensures correct draw order: units first, then UI overlays.
        """
        units = board_snapshot["units"]

        # --- 1️⃣ Draw all unit sprites first ---
        for u in units:
            unit_type = UnitType[u["name"].upper()]
            team = u["team"] if isinstance(u["team"], TeamType) else TeamType(u["team"])

            rect = pygame.Rect(
                u["x"] * self.cell_size + SIDEBAR_WIDTH,
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

            # Cache screen rect for later overlay draws
            u["_rect"] = rect

        # --- 2️⃣ Draw overlays (HP bar + damage) separately ---
        for u in units:
            rect = u["_rect"]
            if "max_hp" in u:
                self._draw_health_bar(screen, u, rect)
            self._draw_damage_number(screen, u, rect)

        # --- 3️⃣ Highlight selected unit on top of everything ---
        if selected_id is not None:
            selected = next((u for u in units if u["id"] == selected_id), None)
            if selected:
                rect = selected["_rect"]
                pygame.draw.rect(screen, (255, 230, 80), rect, width=3, border_radius=8)

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

    def draw_sidebar(self, screen, board_snapshot, selected_id, is_player_turn=False):
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

        # --- Turn indicator ---
        if is_player_turn:
            font, color = self.fonts.get("sidebar")
            turn_surf = font.render("It's your turn!", True, (0, 120, 0))
        else:
            font, color = self.fonts.get("sidebar")
            turn_surf = font.render("Enemy turn...", True, (150, 0, 0))

        screen.blit(turn_surf, (20, y))
        y += 40  # Add spacing below the text

        # --- Selected unit info ---
        if selected_id is not None:
            selected = next(
                (u for u in board_snapshot["units"] if u["id"] == selected_id), None
            )
            if selected:
                # Unit name
                font, color = self.fonts.get("sidebar")
                name_surf = font.render(
                    f"{selected['name'].capitalize()}", True, color=color
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
                    font, color = self.fonts.get("sidebar")
                    surf = font.render(f"{label}: {value}", True, color=color)
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

            font, color = self.fonts.get("sidebar")
            label = font.render(text, True, color=color)
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
            font, color = self.fonts.get("sidebar")
            terr_surf = font.render(bonus_text, True, color=color)
            screen.blit(terr_surf, (20, y))

    def handle_sidebar_click(self, pos) -> str | None:
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
