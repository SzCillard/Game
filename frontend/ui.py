# frontend/ui.py
from typing import TYPE_CHECKING, Any, Dict, List, Optional
import pygame

if TYPE_CHECKING:
    from api.api import GameAPI

from utils.constants import TeamType, SIDEBAR_WIDTH
from utils.helpers import pixel_to_grid


class UI:
    def __init__(self, cell_size: int):
        self.cell_size = cell_size

    # ------------------------------
    # Start Menu
    # ------------------------------
    def start_menu(self, screen, font) -> Any:
        """
        Show a start menu and return chosen option.
        Returns: 'start_game' or 'quit'
        """
        running = True
        selected_option = 0
        options = ["Start Game", "Quit"]
        clock = pygame.time.Clock()

        while running:
            screen.fill((30, 30, 40))
            sw, sh = screen.get_size()
            mouse_x, mouse_y = pygame.mouse.get_pos()

            # Title
            title_surf = font.render("Commanders' Arena", True, (255, 220, 100))
            screen.blit(
                title_surf, (sw // 2 - title_surf.get_width() // 2, sh // 4 - 60)
            )

            # Draw buttons
            for i, option in enumerate(options):
                btn_width, btn_height = 220, 50
                btn_x = sw // 2 - btn_width // 2
                btn_y = sh // 2 - 40 + i * 80
                btn_rect = pygame.Rect(btn_x, btn_y, btn_width, btn_height)

                # Hover effect
                if btn_rect.collidepoint(mouse_x, mouse_y):
                    color = (255, 230, 80)
                    selected_option = i
                else:
                    color = (200, 200, 200)

                pygame.draw.rect(screen, color, btn_rect, border_radius=12)

                # Text
                text_surf = font.render(option, True, (10, 10, 10))
                screen.blit(
                    text_surf,
                    (
                        btn_x + btn_width // 2 - text_surf.get_width() // 2,
                        btn_y + btn_height // 2 - text_surf.get_height() // 2,
                    ),
                )

            pygame.display.flip()

            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"

                if event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_DOWN, pygame.K_s]:
                        selected_option = (selected_option + 1) % len(options)
                    elif event.key in [pygame.K_UP, pygame.K_w]:
                        selected_option = (selected_option - 1) % len(options)
                    elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                        return options[selected_option].lower().replace(" ", "_")

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    return options[selected_option].lower().replace(" ", "_")

            clock.tick(30)

    # ------------------------------
    # Game Input
    # ------------------------------
    def handle_event(
        self,
        event: pygame.event.Event,
        units_snapshot: List[Dict[str, Any]],
        selected_id: Optional[int],
    ) -> Optional[Dict[str, Any]]:
        """
        Process a Pygame event and return an action dict if applicable.
        Handles selecting, moving, and attacking units.
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            px, py = event.pos

            # Ignore clicks in the sidebar
            if px < SIDEBAR_WIDTH:
                return None

            # Adjust for sidebar offset
            x, y = pixel_to_grid(px - SIDEBAR_WIDTH, py, self.cell_size)

            # Find unit at clicked position
            target = next(
                (u for u in units_snapshot if u["x"] == x and u["y"] == y), None
            )
            selected = next((u for u in units_snapshot if u["id"] == selected_id), None)

            # No unit currently selected: try to select own unit
            if selected is None:
                if (
                    target
                    and target["team"] == TeamType.PLAYER
                    and not target["has_acted"]
                ):
                    return {"type": "select", "selected_id": target["id"]}
            else:
                # Unit already selected
                if target:
                    if target["team"] != selected["team"]:
                        # Attack enemy
                        return {
                            "type": "attack",
                            "attacker_id": selected["id"],
                            "defender_id": target["id"],
                        }
                    else:
                        # Switch selection to another friendly unit
                        if not target["has_acted"]:
                            return {"type": "select", "selected_id": target["id"]}
                        return None
                else:
                    # Move to empty cell
                    return {"type": "move", "unit_id": selected["id"], "to": (x, y)}

        return None

    # ------------------------------
    # Apply Actions
    # ------------------------------
    def apply_action(
        self, action: Dict[str, Any], api: "GameAPI"
    ) -> Dict[str, Optional[int]]:
        """
        Apply the given action through the API and return updated selection.
        """
        kind = action.get("type")

        if kind == "select":
            return {"selected_id": action["selected_id"]}

        elif kind == "move":
            unit = next(u for u in api.get_units() if u.id == action["unit_id"])
            x, y = action["to"]
            api.request_move(unit, x, y)
            return {"selected_id": unit.id}  # Keep selection on moved unit

        elif kind == "attack":
            attacker = next(u for u in api.get_units() if u.id == action["attacker_id"])
            defender = next(u for u in api.get_units() if u.id == action["defender_id"])
            api.request_attack(attacker, defender)
            return {"selected_id": None}  # Clear selection after attack

        return {"selected_id": None}
