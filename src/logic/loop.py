from bakasable.think import on_loop
from bakasable.entities import MapChunk
from bakasable.logic.chunk import get_chunk_range


@on_loop(priority=10, type='global')
def load_interest_zone(context, **kw):
    interested_chunks = set()

    for entity in context.object_store.store.values():
        if not isinstance(entity, MapChunk):
            interested_chunks.update(get_chunk_range(
                entity.x - entity.interest_zone,
                entity.y - entity.interest_zone,
                entity.x + entity.interest_zone,
                entity.y + entity.interest_zone))

    context.entities_mngt.load_chunks(interested_chunks)
