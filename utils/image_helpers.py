import os
from typing import Optional, Tuple

import pygame

from utils.constants import TeamType, UnitType


def load_unit_images(cell_size: int):
    """
    Preload all unit images for both teams.

    Returns:
        dict: Nested dictionary of format:
              images[UnitType][TeamType] = pygame.Surface
    """
    images = {}
    base_path = os.path.join("assets/images")

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
                img = pygame.transform.scale(img, (cell_size, cell_size))
                images[unit][team] = img
            else:
                print(f"⚠️ Missing image: {path}")
                images[unit][team] = None
    return images


def load_single_image(path: str, size: Tuple[int, int]) -> Optional[pygame.Surface]:
    """Load and scale a single image from the given path."""
    if os.path.exists(path):
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.scale(img, size)
        return img
    else:
        print(f"⚠️ Missing image: {path}")
        return None
