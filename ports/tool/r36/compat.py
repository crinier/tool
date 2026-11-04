"""Compatibilita' con pygame 1.9 (quello che apt installa su sistemi vecchi,
es. ArkOS basato su Ubuntu 19.10). Va importato prima di tutto il resto."""
import pygame

PYGAME2 = pygame.version.vernum[0] >= 2

# eventi di collegamento a caldo del gamepad: non esistono in pygame 1.9
if not hasattr(pygame, "JOYDEVICEADDED"):
    pygame.JOYDEVICEADDED = -1001
    pygame.JOYDEVICEREMOVED = -1002

if not PYGAME2:
    _rect = pygame.draw.rect

    def _rect_compat(surface, color, rect, width=0, border_radius=0, **_):
        # pygame 1.9 non sa fare gli angoli arrotondati: angoli dritti
        return _rect(surface, color, rect, width)

    pygame.draw.rect = _rect_compat


def joy_id(j):
    return j.get_instance_id() if hasattr(j, "get_instance_id") else j.get_id()
