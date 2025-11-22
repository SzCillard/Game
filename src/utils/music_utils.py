# utils/music_utils.py

import pygame

from utils.path_utils import get_asset_path


def _stop_music():
    pygame.mixer.music.fadeout(2000)
    pygame.mixer.music.stop()


def play_music(path: str, volume: float = 0.4):
    _stop_music()
    pygame.mixer.init()
    pygame.mixer.music.load(get_asset_path(path))
    pygame.mixer.music.set_volume(volume)
    pygame.mixer.music.play(-1)


def play_menu_music():
    play_music(
        "assets/music/menu/Teutoburg.mp3",
        volume=0.5,
    )


def play_battle_music():
    play_music(
        "assets/music/battle/Under Siege (Ancient Epic Battle Music).mp3", volume=0.5
    )
