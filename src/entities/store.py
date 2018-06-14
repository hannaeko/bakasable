import collections
import logging

from bakasable import entities


logger = logging.getLogger(__name__)


class ObjectStore():
    def __init__(self, context):
        self.context = context
        self.store = {}  # {chunk_id: {entity_id: entity}}
        self.coordinated = set()

    def add(self, obj):
        if isinstance(obj, collections.Iterable):
            for o in obj:
                self.add(o)
        elif isinstance(obj, entities.Chunk):
            self.add(obj.map)
            self.add(obj.entities)
        else:
            self.store[obj.uid] = obj
            logger.debug('Added %d to local store', obj.uid)
            if self.context.peer_store.get_closest_uid(obj.uid) == self.context.peer_id:
                self.coordinated.add(obj.uid)
                logger.debug('Added %d to coordinated entities', obj.uid)

    def remove(self, uid):
        if uid in self.store:
            del self.store['uid']
            logger.debug('Removed %d from local store', uid)
        if uid in self.coordinated:
            self.coordinated.remove(uid)
            logger.debug('Removed %d from coordinated entities', uid)

    def get(self, uid, expend_chunk=True):
        entity = self.store.get(uid, None)
        if expend_chunk and isinstance(entity, entities.MapChunk):
            return entities.Chunk(
                map=entity,
                entities=self.get_entities_in_chunk(entity.x, entity.y))
        return entity

    def get_chunk(self, chunk_x, chunk_y):
        chunk_uid = entities.MapChunk.gen_uid(
            self.context.game_id, chunk_x, chunk_y)
        return self.get(chunk_uid)

    def get_entities_in_chunk(self, chunk_x, chunk_y):
        x, y = 15 * chunk_x, 15 * chunk_y
        x_max, y_max = x + 15, y + 15
        for entity in self.store.values():
            if not isinstance(entity, entities.MapChunk) and \
                entity.x >= x and entity.y >= y and \
                    entity.x <= x_max and entity.y <= y_max:
                yield entity

    def is_local_coordinator(self, uid):
        return uid in self.coordinated

    def set_local_coordinator(self, uid, coordinator):
        if coordinator:
            self.coordinated.add(uid)
            logger.debug('Added %d to coordinated entities', uid)
        elif uid in self.coordinated:
            logger.debug('Removed %d from coordinated entities', uid)
            self.coordinated.remove(uid)
