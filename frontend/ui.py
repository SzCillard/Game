from typing import TYPE_CHECKING, Any, Dict, List, Optional

import pygame

if TYPE_CHECKING:
    from api.api import GameAPI
    from frontend.renderer import Renderer

from utils.constants import SIDEBAR_WIDTH, TeamType
from utils.helpers import pixel_to_grid


class UI:
    def __init__(self, cell_size: int, renderer: "Renderer"):
        self.cell_size = cell_size
        self.renderer = renderer

    # ------------------------------
    # Start Menu
    # ------------------------------
    def start_menu(self, screen, font) -> Any:
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

                if btn_rect.collidepoint(mouse_x, mouse_y):
                    color = (255, 230, 80)
                    selected_option = i
                else:
                    color = (200, 200, 200)

                pygame.draw.rect(screen, color, btn_rect, border_radius=12)

                text_surf = font.render(option, True, (10, 10, 10))
                screen.blit(
                    text_surf,
                    (
                        btn_x + btn_width // 2 - text_surf.get_width() // 2,
                        btn_y + btn_height // 2 - text_surf.get_height() // 2,
                    ),
                )

            pygame.display.flip()

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

            clock.tick(60)

    # ------------------------------
    # Game Input
    # ------------------------------
    def handle_event(
        self,
        event: pygame.event.Event,
        units_snapshot: List[Dict[str, Any]],
        selected_id: Optional[int],
    ) -> Optional[Dict[str, Any]]:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            px, py = event.pos

            # Sidebar button clicks
            if px < SIDEBAR_WIDTH and self.renderer:
                clicked = self.renderer.handle_sidebar_click((px, py))
                if clicked == "Quit":
                    return {"type": "quit"}
                elif clicked == "Menu":
                    return {"type": "menu"}
                elif clicked == "Help":
                    return {"type": "help"}
                return None

            # Adjust for sidebar offset
            x, y = pixel_to_grid(px - SIDEBAR_WIDTH, py, self.cell_size)
            target = next(
                (u for u in units_snapshot if u["x"] == x and u["y"] == y), None
            )
            selected = next((u for u in units_snapshot if u["id"] == selected_id), None)

            if selected is None:
                if (
                    target
                    and target["team"] == TeamType.PLAYER
                    and not target["has_acted"]
                ):
                    return {"type": "select", "selected_id": target["id"]}
            else:
                if target:
                    if target["team"] != selected["team"]:
                        return {
                            "type": "attack",
                            "attacker_id": selected["id"],
                            "defender_id": target["id"],
                        }
                    else:
                        if not target["has_acted"]:
                            return {"type": "select", "selected_id": target["id"]}
                        return None
                else:
                    return {"type": "move", "unit_id": selected["id"], "to": (x, y)}

        return None

    # ------------------------------
    # Apply Actions
    # ------------------------------
    def apply_action(
        self, action: Dict[str, Any], api: "GameAPI"
    ) -> Dict[str, Optional[int]]:
        kind = action.get("type")

        if kind == "select":
            return {"selected_id": action["selected_id"]}

        elif kind == "move":
            unit = next(u for u in api.get_units() if u.id == action["unit_id"])
            x, y = action["to"]
            api.request_move(unit, x, y)
            return {"selected_id": unit.id}

        elif kind == "attack":
            attacker = next(u for u in api.get_units() if u.id == action["attacker_id"])
            defender = next(u for u in api.get_units() if u.id == action["defender_id"])
            api.request_attack(attacker, defender)
            return {"selected_id": None}

        elif kind == "quit":
            return {"selected_id": None, "quit_requested": True}

        elif kind == "menu":
            return {"selected_id": None, "menu_requested": True}

        elif kind == "help":
            print("📖 Help button clicked")
            return {"selected_id": None, "help_requested": True}

        return {"selected_id": None}
