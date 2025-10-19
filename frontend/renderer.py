import pygame

from utils.button_manager import ButtonManager, ButtonType
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
    """

    def __init__(self, cell_size: int):
        self.cell_size = cell_size
        self.unit_images = load_unit_images(cell_size=cell_size)
        self.fonts = FontManager()
        self.buttons = ButtonManager()  # centralized button manager

    # ------------------------------
    # Start Menu
    # ------------------------------

    def draw_start_menu(
        self, screen: pygame.Surface, selected_index: int, options: list[str]
    ) -> None:
        """Render the main menu screen."""
        screen.fill(Color.BLACK.value)
        sw, sh = screen.get_size()
        mouse_pos = pygame.mouse.get_pos()

        # --- Title ---
        font, color = self.fonts.get("title")
        title_surf = font.render("Commanders' Arena", True, color=color)
        screen.blit(title_surf, (sw // 2 - title_surf.get_width() // 2, sh // 4 - 60))

        # --- Buttons ---
        self.buttons.buttons.clear()
        btn_width, btn_height = 220, 50

        for i, option in enumerate(options):
            btn_x = sw // 2 - btn_width // 2
            btn_y = sh // 2 - 40 + i * 80
            rect = pygame.Rect(btn_x, btn_y, btn_width, btn_height)
            btn_type = ButtonType.MENU if option.lower() != "quit" else ButtonType.QUIT
            self.buttons.register(option, rect, btn_type)
            self.buttons.draw_button(screen, option, option, mouse_pos)

    # ------------------------------
    # Draft Menu
    # ------------------------------

    def draw_draft_screen(
        self, screen, available_units, selected_units, funds_left
    ) -> None:
        """Draw pre-battle army selection screen."""
        screen.fill((25, 25, 25))
        sw, sh = screen.get_size()
        font_title, color_title = self.fonts.get("title")
        font_text, color_text = self.fonts.get("sidebar")
        mouse_pos = pygame.mouse.get_pos()
        self.buttons.buttons.clear()

        # --- Title ---
        title = font_title.render("Select Your Army", True, color_title)
        screen.blit(title, (sw // 2 - title.get_width() // 2, 40))

        # --- Funds display ---
        funds_text = font_text.render(
            f"Funds left: {funds_left}", True, (255, 255, 150)
        )
        screen.blit(funds_text, (sw // 2 - funds_text.get_width() // 2, 100))

        # --- Column headers ---
        headers = ["Unit", "Cost", "HP", "Armor", "ATK", "Range", "Mov"]
        header_x_positions = [150, 360, 430, 490, 550, 610, 670]
        for hx, header in zip(header_x_positions, headers):
            hsurf = font_text.render(header, True, (200, 200, 200))
            screen.blit(hsurf, (hx, 150))

        # --- Layout ---
        start_y = 180
        row_height = 55
        btn_w, btn_h = 60, 30

        # --- Units ---
        for i, (name, data) in enumerate(available_units.items()):
            y = start_y + i * row_height

            # Background stripes
            if i % 2 == 0:
                pygame.draw.rect(
                    screen, (35, 35, 35), (130, y - 8, sw - 280, row_height)
                )

            # Unit name
            name_surf = font_text.render(name, True, Color.LIGHT_GRAY.value)
            screen.blit(name_surf, (150, y))

            # Stats
            stats = [
                data.get("cost", 0),
                data.get("health", 0),
                data.get("armor", 0),
                data.get("attack_power", 0),
                data.get("attack_range", 0),
                data.get("move_range", 0),
            ]
            for val, x in zip(stats, header_x_positions[1:]):
                surf = font_text.render(str(val), True, Color.LIGHT_GRAY.value)
                screen.blit(surf, (x, y))

            # Buttons
            add_rect = pygame.Rect(sw - 190, y, btn_w, btn_h)
            rem_rect = pygame.Rect(sw - 120, y, btn_w, btn_h)

            self.buttons.register(f"add_{name}", add_rect, ButtonType.ADD)
            self.buttons.register(f"rem_{name}", rem_rect, ButtonType.REMOVE)
            self.buttons.draw_button(screen, f"add_{name}", "+", mouse_pos)
            self.buttons.draw_button(screen, f"rem_{name}", "-", mouse_pos)

        # --- Player’s army ---
        screen.blit(
            font_text.render("Your Army:", True, Color.WHITE.value), (150, sh - 180)
        )
        y = sh - 150
        for unit in selected_units:
            unit_text = font_text.render(unit, True, (200, 200, 200))
            screen.blit(unit_text, (180, y))
            y += 28

        # --- Start button ---
        start_rect = pygame.Rect(sw // 2 - 100, sh - 70, 200, 50)
        self.buttons.register("start_battle", start_rect, ButtonType.START_GAME)
        self.buttons.draw_button(screen, "start_battle", "Start Battle", mouse_pos)

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
                pygame.draw.rect(
                    screen, Color.YELLOW.value, rect, width=3, border_radius=8
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

    def draw_sidebar(self, screen, board_snapshot, selected_id, is_player_turn=False):
        """Render sidebar with info + menu buttons."""
        sidebar_rect = pygame.Rect(0, 0, SIDEBAR_WIDTH, SCREEN_H)
        pygame.draw.rect(screen, (230, 230, 230), sidebar_rect)
        pygame.draw.line(
            screen, (100, 100, 100), (SIDEBAR_WIDTH, 0), (SIDEBAR_WIDTH, SCREEN_H), 2
        )

        y = 20
        font, color = self.fonts.get("sidebar")
        turn_text = "It's your turn!" if is_player_turn else "Enemy turn..."
        turn_color = (0, 120, 0) if is_player_turn else (150, 0, 0)
        turn_surf = font.render(turn_text, True, turn_color)
        screen.blit(turn_surf, (20, y))
        y += 40

        # --- Unit info ---
        if selected_id is not None:
            selected = next(
                (u for u in board_snapshot["units"] if u["id"] == selected_id), None
            )
            if selected:
                name_surf = font.render(selected["name"].capitalize(), True, color)
                screen.blit(name_surf, (20, y))
                y += 30
                stats = [
                    ("HP", selected["health"]),
                    ("Move", selected["move_points"]),
                    ("ATK", selected["attack_power"]),
                    ("Range", selected["attack_range"]),
                ]
                for label, val in stats:
                    s = font.render(f"{label}: {val}", True, color)
                    screen.blit(s, (20, y))
                    y += 30
                self._draw_terrain_bonus(board_snapshot, selected, screen, y)

        # --- Menu buttons ---
        menu_items = ["End Turn", "Menu", "Quit", "Help"]
        btn_width, btn_height = SIDEBAR_WIDTH - 40, 40
        menu_y = SCREEN_H - (len(menu_items) * (btn_height + 10)) - 20
        mouse_pos = pygame.mouse.get_pos()
        self.buttons.buttons.clear()

        for i, label in enumerate(menu_items):
            rect = pygame.Rect(
                20, menu_y + i * (btn_height + 10), btn_width, btn_height
            )
            btn_type = (
                ButtonType.SIDEBAR if label.lower() != "quit" else ButtonType.QUIT
            )
            self.buttons.register(label, rect, btn_type)
            self.buttons.draw_button(screen, label, label, mouse_pos)

    # ------------------------------
    # Terrain Bonus (unchanged)
    # ------------------------------

    def _draw_terrain_bonus(self, board_snapshot, selected, screen, y):
        tiles = board_snapshot["tiles"]
        ux, uy = selected["x"], selected["y"]
        if 0 <= uy < len(tiles) and 0 <= ux < len(tiles[0]):
            tile = tiles[uy][ux]
            def_bonus = TERRAIN_DEFENSE_BONUS.get(tile, 0)
            atk_bonus = TERRAIN_ATTACK_BONUS.get(tile, 0)
            tile_name = tile.name.capitalize() if hasattr(tile, "name") else str(tile)
            parts = []
            if def_bonus:
                parts.append(f"{int(def_bonus * 100)}% DEF")
            if atk_bonus:
                parts.append(f"{int(atk_bonus * 100)}% ATK")
            if not parts:
                parts.append("No bonus")
            bonus_text = f"{tile_name}: {', '.join(parts)}"
            font, color = self.fonts.get("sidebar")
            screen.blit(font.render(bonus_text, True, color), (20, y))

    # ------------------------------
    # Click Handling
    # ------------------------------

    def handle_click(self, pos):
        """Return the name of the clicked button if any."""
        return self.buttons.was_clicked(pos)
