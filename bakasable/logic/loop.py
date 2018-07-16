import random
import logging
import math

import pygame

from bakasable.think import on_loop
from bakasable.entities import (
    UpdatableGameObject,
    DrawableGameObject,
    MapChunk,
    Sheep,
    Player,
    mngt
)
from bakasable.logic.chunk import get_chunk_range
from bakasable import const


logger = logging.getLogger(__name__)


@on_loop(priority=10, type='global')
def load_interest_zone(context, **kw):
    interested_chunks = set()
    player_interest = set()

    for uid in context.object_store.coordinated:
        entity = context.object_store.get(uid, expend_chunk=False)
        # TODO: subscribe for update for entities in coordinated chunk
        if not isinstance(entity, MapChunk):
            interest_zone = get_chunk_range(
                entity.x - entity.interest_zone,
                entity.y - entity.interest_zone,
                entity.x + entity.interest_zone,
                entity.y + entity.interest_zone)
            if entity.uid == context.peer_id:
                player_interest.update(interest_zone)
            elif entity.is_fresh:
                interested_chunks.update(interest_zone)

    mngt.load_chunks(interested_chunks | player_interest)
    mngt.subscribe_updates(
        interested_chunks | player_interest, player_interest)


@on_loop(priority=200, target=Sheep)
def random_walk_sheep(context, target, **kw):
    if target.rest:
        target.rest -= 1
        return

    action = random.choices([0, 1, 2], [100, 1, 10])[0]

    if action == 1:  # change direction
        target.change_direction()
    elif action == 2:
        target.rest = random.randint(20, 40)
        target.change_direction()
    else:
        new_pos = pygame.math.Vector2(target.direction)
        new_pos.x -= target.x
        new_pos.y -= target.y
        try:
            new_pos.normalize_ip()
        except ValueError:
            new_pos = pygame.math.Vector2(0)
        new_pos *= const.SHEEP_WALKING_SPEED
        target.x += new_pos.x
        target.y += new_pos.y
        if math.isclose(target.x, target.direction.x,
                        abs_tol=const.SHEEP_WALKING_SPEED) or \
                math.isclose(target.y, target.direction.y,
                             abs_tol=const.SHEEP_WALKING_SPEED):
            target.change_direction()


@on_loop(priority=200, target=Player)
def update_player(context, target, **kw):
    target.x += target.speed.x * context.dt
    target.y += target.speed.y * context.dt


@on_loop(priority=200, target=DrawableGameObject)
def update_sprite(context, target, **kw):
    target.frame_index = target.sprite.update(context.dt)


@on_loop(priority=300, target=UpdatableGameObject)
def dispatch_update(target, **kw):
    mngt.emit_entity_state_change(target)
    new_chunk = target.chunk_changed()
    target.update()
    if new_chunk:
        mngt.send_enter_chunk_interest(target)
