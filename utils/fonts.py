# utils/fonts.py
from enum import Enum, IntEnum

import pygame

from utils.constants import Color


class FontSize(IntEnum):
    S = 16
    M = 24
    L = 32
    XL = 40


class FontType(Enum):
    MENU = "menu"
    SIDEBAR = "sidebar"
    DAMAGE = "damage"
    TITLE = "title"


FONT_FAMILIES = {
    FontType.MENU: "Calibri",
    FontType.SIDEBAR: "Arial",
    FontType.DAMAGE: "Comic Sans MS",
    FontType.TITLE: "Verdana",
}
FONT_COLORS = {
    FontType.MENU: Color.BLACK.value,
    FontType.SIDEBAR: Color.BLACK.value,
    FontType.DAMAGE: Color.RED.value,
    FontType.TITLE: Color.YELLOW.value,
}


class FontManager:
    def __init__(self):
        pygame.font.init()

        # Preload fonts (change families or sizes here)
        self.fonts = {
            "menu": pygame.font.SysFont(FONT_FAMILIES[FontType.MENU], FontSize.L),
            "sidebar": pygame.font.SysFont(FONT_FAMILIES[FontType.SIDEBAR], FontSize.S),
            "damage": pygame.font.SysFont(FONT_FAMILIES[FontType.DAMAGE], FontSize.S),
            "title": pygame.font.SysFont(FONT_FAMILIES[FontType.TITLE], FontSize.XL),
        }

        # Default colors for each
        self.colors = {
            "menu": FONT_COLORS[FontType.MENU],
            "sidebar": FONT_COLORS[FontType.SIDEBAR],
            "damage": FONT_COLORS[FontType.DAMAGE],
            "title": FONT_COLORS[FontType.TITLE],
        }

    def get(self, type: str):
        """Return (font, color) tuple for a given category name."""
        font = self.fonts.get(type, self.fonts["menu"])
        color = self.colors.get(type, (0, 0, 0))
        return font, color
