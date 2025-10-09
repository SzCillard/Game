import pygame


def _stop_music():
    """Stop all currently playing music."""
    pygame.mixer.music.fadeout(2000)  # fade out over 2 seconds
    pygame.mixer.music.stop()


def play_music(path: str, volume: float = 0.4):
    _stop_music()
    pygame.mixer.init()
    pygame.mixer.music.load(path)
    pygame.mixer.music.set_volume(volume)
    pygame.mixer.music.play(-1)  # -1 means loop indefinitely


def play_menu_music():
    play_music(
        "assets/music/menu/Teutoburg (Ancient Germania Music - The Battle of Teutoburg Forest).mp3",
        volume=0.5,
    )


def play_battle_music():
    play_music(
        "assets/music/battle/Under Siege (Ancient Epic Battle Music).mp3", volume=0.5
    )
