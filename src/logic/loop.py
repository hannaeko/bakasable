import random
import logging

from bakasable.think import on_loop
from bakasable.entities import (
    UpdatableGameObject,
    MapChunk,
    Sheep,
    Player,
    mngt
)
from bakasable.logic.chunk import get_chunk_range


logger = logging.getLogger(__name__)


@on_loop(priority=10, type='global')
def load_interest_zone(context, **kw):
    interested_chunks = set()

    for uid in context.object_store.coordinated:
        entity = context.object_store.get(uid, expend_chunk=False)
        # TODO: subscribe for update for entities in coordinated chunk
        if not isinstance(entity, MapChunk):
            interested_chunks.update(get_chunk_range(
                entity.x - entity.interest_zone,
                entity.y - entity.interest_zone,
                entity.x + entity.interest_zone,
                entity.y + entity.interest_zone))

    mngt.load_chunks(interested_chunks)
    mngt.subscribe_updates(interested_chunks)


@on_loop(priority=100, type='global')
def update_sprite(context, **kw):
    for entity in context.object_store.store.values():
        if entity.sprite_name:
            entity.sprite.update(context.dt)


@on_loop(priority=200, target=Sheep)
def random_walk_sheep(target, **kw):
    if random.random() > 0.7:
        target.x += random.choices([1, -1])[0]/5
        target.y += random.choices([1, -1])[0]/5


@on_loop(priority=200, target=Player)
def update_player(context, target, **kw):
    target.x += target.speed.x * context.dt
    target.y += target.speed.y * context.dt


@on_loop(priority=300, target=UpdatableGameObject)
def dispatch_update(target, **kw):
    mngt.emit_entity_state_change(target)
    new_chunk = target.chunk_changed()
    target.update()
    if new_chunk:
        mngt.send_enter_chunk_interest(target)
