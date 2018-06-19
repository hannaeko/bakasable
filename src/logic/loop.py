from bakasable.think import on_loop
from bakasable.entities import MapChunk
from bakasable.logic.chunk import get_chunk_range


@on_loop(priority=10, type='global')
def load_interest_zone(context, **kw):
    interested_chunks = set()

    for uid in context.object_store.coordinated:
        entity = context.object_store.get(uid, expend_chunk=False)
        if not isinstance(entity, MapChunk):
            interested_chunks.update(get_chunk_range(
                entity.x - entity.interest_zone,
                entity.y - entity.interest_zone,
                entity.x + entity.interest_zone,
                entity.y + entity.interest_zone))

    context.entities_mngt.load_chunks(interested_chunks)
    context.entities_mngt.subscribe_updates(interested_chunks)


@on_loop(priority=100, type='global')
def update_sprite(context, **kw):
    for entity in context.object_store.store.values():
        if hasattr(entity, '_sprite'):
            entity._sprite.update(context.dt)
