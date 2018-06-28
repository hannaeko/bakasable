import pygame

from bakasable.think import on_event


@on_event(type=pygame.QUIT)
def quit_game(context, **kw):
    context.carry_on = False
