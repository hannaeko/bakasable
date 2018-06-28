import collections
import logging

from bakasable import entities
from bakasable.entities import mngt


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
            if obj.uid in self.coordinated:
                logger.debug(
                    'Entity %d already in store and coordinated, skipping',
                    obj.uid)
            else:
                logger.debug('Added %d to local store', obj.uid)
                logger.debug('Old = %s ; New = %s',
                             self.store.get(obj.uid), obj)
                self.store[obj.uid] = obj
                self.set_local_coordinator(obj.uid)

    def remove(self, uid):
        if uid in self.store:
            self.store.pop('uid', None)
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
                    entity.x < x_max and entity.y < y_max:
                yield entity

    def is_local_coordinator(self, uid):
        return uid in self.coordinated

    def set_local_coordinator(self, uid, coordinator=None):
        if uid not in self.store:
            return

        if coordinator is None:
            coordinator = self.context \
                .peer_store.get_closest_uid(uid) == self.context.peer_id

        if coordinator and uid not in self.coordinated:
            self.coordinated.add(uid)
            if hasattr(self.store[uid], 'active'):
                self.store[uid].active = True
            logger.debug('Added %d to coordinated entities', uid)
            mngt.send_coordinator_change_interest(uid)
        elif not coordinator and uid in self.coordinated:
            logger.debug('Removed %d from coordinated entities', uid)
            self.coordinated.remove(uid)
            if hasattr(self.store[uid], 'active'):
                self.store[uid].active = False
            entity = self.get(uid, expend_chunk=False)

            if isinstance(entity, entities.MapChunk):
                mngt.send_chunk_update_interest(entity.x, entity.y, uid)
            else:
                mngt.send_entity_update_interest(uid)
