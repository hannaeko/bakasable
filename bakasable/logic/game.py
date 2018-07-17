import pygame

from bakasable.think import on_event, on_action
from bakasable.const import PLAYER_WALKING_SPEED, actions
from bakasable.entities import MapChunk, Sheep, Player, mngt


@on_event(type=pygame.QUIT)
def quit_game(context, **kw):
    context.carry_on = False


@on_event(type=pygame.KEYDOWN)
def start_moving_player(context, key, **kw):
    player = context.object_store.get(context.peer_id)
    if key == pygame.K_UP:
        player.speed.y -= PLAYER_WALKING_SPEED
    if key == pygame.K_DOWN:
        player.speed.y += PLAYER_WALKING_SPEED
    if key == pygame.K_LEFT:
        player.speed.x -= PLAYER_WALKING_SPEED
    if key == pygame.K_RIGHT:
        player.speed.x += PLAYER_WALKING_SPEED
    if player.speed.x != 0 or player.speed.y != 0:
        player.sprite.start_animation()


@on_event(type=pygame.KEYUP)
def stop_moving_player(context, key, **kw):
    player = context.object_store.get(context.peer_id)
    if key == pygame.K_UP:
        player.speed.y += PLAYER_WALKING_SPEED
    if key == pygame.K_DOWN:
        player.speed.y -= PLAYER_WALKING_SPEED
    if key == pygame.K_LEFT:
        player.speed.x += PLAYER_WALKING_SPEED
    if key == pygame.K_RIGHT:
        player.speed.x -= PLAYER_WALKING_SPEED
    if player.speed.x == 0 and player.speed.y == 0:
        player.sprite.stop_animation()


@on_event(type=pygame.KEYDOWN, key=pygame.K_SPACE)
def primary_action(context, **kw):
    player = context.object_store.get(context.peer_id)
    x = player.x + 3
    targets = [entity for entity in context.object_store.store.values()
               if not isinstance(entity, MapChunk) and
               entity.uid != context.peer_id and
               entity.x >= player.x and entity.x < x and
               abs(entity.y - player.y) < 1]
    try:
        target = targets[0]
        mngt.emit_action(actions.PRIMARY, target, player)
    except IndexError:
        pass


@on_action(type=actions.PRIMARY, target=Sheep, sender=Player)
def shear_sheep(target, **kw):
    print('Sheep shorn')
