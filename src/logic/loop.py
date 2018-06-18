import numpy as np

from bakasable.think import on_loop
from bakasable.entities import MapChunk


@on_loop(priority=10, type='global')
def load_interest_zone(context, **kw):
    interested_chunks = set()

    for entity in context.object_store.store.values():
        if not isinstance(entity, MapChunk):
            x_range = range((entity.x - entity.interest_zone) // 15,
                            (entity.x + entity.interest_zone) // 15 + 1)
            y_range = range((entity.y - entity.interest_zone) // 15,
                            (entity.y + entity.interest_zone) // 15 + 1)

            for chunk_x in x_range:
                for chunk_y in y_range:
                    interested_chunks.add((chunk_x, chunk_y))

    context.entities_mngt.load_chunks(interested_chunks)
