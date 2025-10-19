from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pygame

if TYPE_CHECKING:
    from api.api import GameAPI
    from frontend.renderer import Renderer

from utils.constants import FPS, SIDEBAR_WIDTH, STARTING_FUNDS, UNIT_STATS, TeamType
from utils.helpers import pixel_to_grid


class UI:
    """
    Handles all user interface logic, including menus, in-game input,
    and player interaction with the GameAPI.

    Responsibilities:
    - Displaying and managing the start menu
    - Handling mouse and keyboard input during gameplay
    - Converting UI actions into structured commands
    - Executing those commands via the GameAPI
    """

    def __init__(self, cell_size: int, renderer: Renderer) -> None:
        """
        Initialize the UI system.

        Args:
            cell_size: The pixel size of each board cell.
            renderer: The Renderer responsible for drawing UI and board elements.
        """
        self.cell_size = cell_size
        self.renderer = renderer

    # ------------------------------
    # Start Menu handling
    # ------------------------------

    def start_menu(self, screen: pygame.Surface, font: pygame.font.Font) -> str:
        """Display the start menu and handle user input."""

        options = ["Start Game", "Quit"]
        selected_index = 0
        clock = pygame.time.Clock()

        while True:
            # --- Event handling ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"

                if event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_DOWN, pygame.K_s]:
                        selected_index = (selected_index + 1) % len(options)
                    elif event.key in [pygame.K_UP, pygame.K_w]:
                        selected_index = (selected_index - 1) % len(options)
                    elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                        return options[selected_index].lower().replace(" ", "_")

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Determine if clicked on a button
                    mx, my = pygame.mouse.get_pos()
                    sw, sh = screen.get_size()
                    for i, option in enumerate(options):
                        btn_width, btn_height = 220, 50
                        btn_x = sw // 2 - btn_width // 2
                        btn_y = sh // 2 - 40 + i * 80
                        if (
                            btn_x <= mx <= btn_x + btn_width
                            and btn_y <= my <= btn_y + btn_height
                        ):
                            return options[i].lower().replace(" ", "_")

            # --- Draw the menu ---
            self.renderer.draw_start_menu(screen, selected_index, options)
            pygame.display.flip()
            clock.tick(FPS)

    # ------------------------------
    # Draft / Army Selection Menu
    # ------------------------------

    def draft_menu(self, screen):
        """Display the pre-battle draft/army selection phase."""
        clock = pygame.time.Clock()
        selected_units = []
        funds_left = STARTING_FUNDS

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = event.pos
                    clicked = self.renderer.handle_sidebar_click(pos)

                    # Add unit
                    if clicked and clicked.startswith("add_"):
                        unit_name = clicked.replace("add_", "")
                        cost = UNIT_STATS[unit_name]["cost"]
                        if funds_left >= cost:
                            selected_units.append(unit_name)
                            funds_left -= cost

                    # Remove unit
                    elif clicked and clicked.startswith("rem_"):
                        unit_name = clicked.replace("rem_", "")
                        if unit_name in selected_units:
                            selected_units.remove(unit_name)
                            funds_left += UNIT_STATS[unit_name]["cost"]

                    # Start battle
                    elif clicked == "start_battle" and selected_units:
                        return selected_units

            # Draw draft screen
            self.renderer.draw_draft_screen(
                screen, UNIT_STATS, selected_units, funds_left
            )
            pygame.display.flip()
            clock.tick(FPS)

    # ------------------------------
    # Game Input Handling
    # ------------------------------
    def handle_event(
        self,
        event: pygame.event.Event,
        units_snapshot: list[dict[str, Any]],
        selected_id: int | None,
    ) -> dict[str, Any] | None:
        """
        Process player input events during gameplay.

        Converts mouse clicks into structured action dictionaries that describe
        the player's intent (select, move, attack, etc.).

        Args:
            event: The pygame event being processed.
            units_snapshot: A snapshot of all current units on the board.
            selected_id: ID of the currently selected unit, or None if none is selected.

        Returns:
            A structured action dictionary such as:
                {"type": "select", "selected_id": 3}
                {"type": "move", "unit_id": 3, "to": (x, y)}
                {"type": "attack", "attacker_id": 3, "defender_id": 7}
            Returns None if no actionable input is detected.
        """
        # Handle left mouse click only
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            px, py = event.pos

            # --- Sidebar buttons ---
            if px < SIDEBAR_WIDTH and self.renderer:
                clicked = self.renderer.handle_sidebar_click((px, py))
                if clicked == "End Turn":
                    return {"type": "end_turn"}
                elif clicked == "Menu":
                    return {"type": "menu"}
                elif clicked == "Quit":
                    return {"type": "quit"}
                elif clicked == "Help":
                    return {"type": "help"}
                return None

            # --- Board interaction ---
            # Convert mouse position to grid coordinates (offset by sidebar)
            x, y = pixel_to_grid(px - SIDEBAR_WIDTH, py, self.cell_size)
            target = next(
                (u for u in units_snapshot if u["x"] == x and u["y"] == y), None
            )
            selected = next((u for u in units_snapshot if u["id"] == selected_id), None)

            # --- No unit currently selected: try selecting one ---
            if selected is None:
                if (
                    target
                    and target["team"] == TeamType.PLAYER
                    and not target["has_acted"]
                ):
                    return {"type": "select", "selected_id": target["id"]}

            # --- A unit is selected: decide the next action ---
            else:
                if target:
                    # Attack if enemy unit clicked
                    if target["team"] != selected["team"]:
                        return {
                            "type": "attack",
                            "attacker_id": selected["id"],
                            "defender_id": target["id"],
                        }

                    # Switch to another friendly unit if available
                    elif not target["has_acted"]:
                        return {"type": "select", "selected_id": target["id"]}
                    return None

                # Clicked on an empty tile — attempt to move
                return {"type": "move", "unit_id": selected["id"], "to": (x, y)}

        return None

    # ------------------------------
    # Apply Actions
    # ------------------------------
    def apply_action(
        self, action: dict[str, Any], api: GameAPI
    ) -> dict[str, int | bool | None]:
        """
        Execute the provided player action via the GameAPI.

        This function interprets and applies an action dictionary generated by
        `handle_event()` — e.g., moving a unit, attacking, or ending the turn.

        Args:
            action: The structured action dictionary.
            api: The main game API used to execute game commands.

        Returns:
            A dictionary describing the resulting UI state. Examples:
                {"selected_id": 4}
                {"selected_id": None, "end_turn_requested": True}
                {"selected_id": None, "quit_requested": True}
        """
        kind = action.get("type")

        # --- Selecting a unit ---
        if kind == "select":
            return {"selected_id": action["selected_id"]}

        # --- Moving a unit ---
        elif kind == "move":
            unit = next(u for u in api.get_units() if u.id == action["unit_id"])
            x, y = action["to"]
            api.request_move(unit, x, y)
            return {"selected_id": unit.id}

        # --- Attacking another unit ---
        elif kind == "attack":
            attacker = next(u for u in api.get_units() if u.id == action["attacker_id"])
            defender = next(u for u in api.get_units() if u.id == action["defender_id"])
            api.request_attack(attacker, defender)
            return {"selected_id": None}

        # --- End turn ---
        elif kind == "end_turn":
            return {"selected_id": None, "end_turn_requested": True}

        # --- Open menu ---
        elif kind == "menu":
            return {"selected_id": None, "menu_requested": True}

        # --- Quit game ---
        elif kind == "quit":
            return {"selected_id": None, "quit_requested": True}

        # --- Help ---
        elif kind == "help":
            print("📖 Help button clicked")
            return {"selected_id": None, "help_requested": True}

        # Default fallback (no valid action)
        return {"selected_id": None}
