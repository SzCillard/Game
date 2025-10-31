# utils/image_helpers.py

import os
from typing import Optional, Tuple

import pygame

from utils.constants import TeamType, UnitType
from utils.path_utils import get_asset_path


def load_unit_images(cell_size: int):
    images = {}
    base_path = "assets/images"

    for unit in UnitType:
        images[unit] = {}
        for team in TeamType:
            team_name = "purple" if team == TeamType.PLAYER else "red"
            rel = f"{base_path}/{unit.name.lower()}/{unit.name.lower()}_{team_name}.png"
            path = get_asset_path(rel)

            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                img = pygame.transform.scale(img, (cell_size, cell_size))
                images[unit][team] = img
            else:
                print(f"⚠️ Missing image: {path}")
                images[unit][team] = None
    return images


def load_single_image(path: str, size: Tuple[int, int]) -> Optional[pygame.Surface]:
    full = get_asset_path(path)
    if os.path.exists(full):
        img = pygame.image.load(full).convert_alpha()
        img = pygame.transform.scale(img, size)
        return img
    print(f"⚠️ Missing image: {full}")
    return None
