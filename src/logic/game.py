import pygame

from bakasable.think import on_event
from bakasable.const import PLAYER_WALKING_SPEED


@on_event(type=pygame.QUIT)
def quit_game(context, **kw):
    context.carry_on = False


@on_event(type=pygame.KEYDOWN)
def start_moving_player(context, key, **kw):
    player = context.object_store.get(context.peer_id)
    player.sprite.start_animation()
    if key == pygame.K_UP:
        player.speed.y -= PLAYER_WALKING_SPEED
    if key == pygame.K_DOWN:
        player.speed.y += PLAYER_WALKING_SPEED
    if key == pygame.K_LEFT:
        player.speed.x -= PLAYER_WALKING_SPEED
    if key == pygame.K_RIGHT:
        player.speed.x += PLAYER_WALKING_SPEED


@on_event(type=pygame.KEYUP)
def stop_moving_player(context, key, **kw):
    player = context.object_store.get(context.peer_id)
    if player.speed.x == 0 and player.speed.y == 0:
        player.sprite.stop_animation()
    if key == pygame.K_UP:
        player.speed.y += PLAYER_WALKING_SPEED
    if key == pygame.K_DOWN:
        player.speed.y -= PLAYER_WALKING_SPEED
    if key == pygame.K_LEFT:
        player.speed.x += PLAYER_WALKING_SPEED
    if key == pygame.K_RIGHT:
        player.speed.x -= PLAYER_WALKING_SPEED
