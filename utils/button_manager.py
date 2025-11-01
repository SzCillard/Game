from enum import Enum
from typing import TYPE_CHECKING

import pygame

from utils.constants import Color

if TYPE_CHECKING:
    from utils.font_manager import FontManager


class ButtonType(Enum):
    MENU = "menu"
    SIDEBAR = "sidebar"
    ADD = "add"
    REMOVE = "remove"
    START_GAME = "start_game"
    QUIT = "quit"


BUTTON_TO_FONT_TYPE_MAP = {
    ButtonType.MENU: "menu",
    ButtonType.SIDEBAR: "sidebar",
    ButtonType.ADD: "sidebar",
    ButtonType.REMOVE: "sidebar",
    ButtonType.START_GAME: "menu",
    ButtonType.QUIT: "quit",
}

# ------------------------------
# 🎨 Centralized Button Colors
# ------------------------------

BUTTON_COLORS = {
    ButtonType.MENU: Color.LIGHT_GRAY.value,
    ButtonType.SIDEBAR: Color.ORANGE_DESERT.value,
    ButtonType.ADD: Color.LIGHT_GREEN.value,
    ButtonType.REMOVE: Color.RED.value,
    ButtonType.START_GAME: Color.LIGHT_GREEN.value,
    ButtonType.QUIT: Color.LIGHT_GRAY.value,
}

HOVER_COLORS = {
    ButtonType.MENU: Color.YELLOW.value,
    ButtonType.SIDEBAR: Color.DARK_DESERT.value,
    ButtonType.ADD: Color.DARK_GREEN.value,
    ButtonType.REMOVE: Color.DARK_RED.value,
    ButtonType.START_GAME: Color.DARK_GREEN.value,
    ButtonType.QUIT: Color.YELLOW.value,
}


# ------------------------------
# 🧭 Button Manager
# ------------------------------


class ButtonManager:
    """Handles button drawing, hover effects, and style consistency."""

    def __init__(self, font_manager: "FontManager"):
        self.font_manager = font_manager
        self.buttons = {}  # {name: {"rect": Rect, "type": ButtonType}}

    def register(self, name: str, rect: pygame.Rect, btn_type: ButtonType):
        """Register a button to track for rendering and hover detection."""
        self.buttons[name] = {"rect": rect, "type": btn_type}

    def get_hovered(self, mouse_pos):
        """Return the name of the button being hovered, or None."""
        for name, data in self.buttons.items():
            if data["rect"].collidepoint(mouse_pos):
                return name
        return None

    def draw_button(self, screen, name: str, label: str, mouse_pos):
        """Draw a single button with hover effect."""
        if name not in self.buttons:
            return

        rect = self.buttons[name]["rect"]
        btn_type = self.buttons[name]["type"]

        # Base and hover colors
        base_color = BUTTON_COLORS[btn_type]
        hover_color = HOVER_COLORS[btn_type]
        color = hover_color if rect.collidepoint(mouse_pos) else base_color

        # Draw button
        pygame.draw.rect(screen, color, rect, border_radius=8)
        pygame.draw.rect(screen, Color.DARK_GRAY.value, rect, 2, border_radius=8)

        # Text
        font, color = self.font_manager.get(BUTTON_TO_FONT_TYPE_MAP[btn_type])
        label_surf = font.render(label, True, color)
        screen.blit(
            label_surf,
            (
                rect.centerx - label_surf.get_width() // 2,
                rect.centery - label_surf.get_height() // 2,
            ),
        )

    def draw_all(self, screen, mouse_pos):
        """Draw all registered buttons (no labels)."""
        for name, data in self.buttons.items():
            self.draw_button(screen, name, name, mouse_pos)

    def was_clicked(self, pos) -> str | None:
        """Check if a button was clicked; returns its name or None."""
        for name, data in self.buttons.items():
            if data["rect"].collidepoint(pos):
                return name
        return None
