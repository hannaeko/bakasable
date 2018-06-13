import collections
import logging

import entities


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
            logging.debug('Added %d to local store', obj.uid)
            if self.context.peer_store.get_closest_uid(obj.uid) == self.context.peer_id:
                self.coordinated.add(obj.uid)
                logging.debug('Added %d to coordinated entities', obj.uid)

    def remove(self, uid):
        if uid in self.store:
            del self.store['uid']
            logging.debug('Removed %d from local store', uid)
        if uid in self.coordinated:
            self.coordinated.remove(uid)
            logging.debug('Removed %d from coordinated entities', uid)

    def get(self, uid):
        return self.store.get(uid, None)

    def get_chunk(self, x, y):
        chunk_uid = entities.MapChunk.gen_uid(
            self.context.game_id, x, y)
        return self.get(chunk_uid)

    def is_local_coordinator(self, uid):
        return uid in self.coordinated

    def set_local_coordinator(self, uid, coordinator):
        if coordinator:
            self.coordinated.add(uid)
            logging.debug('Added %d to coordinated entities', uid)
        elif uid in self.coordinated:
            logging.debug('Removed %d from coordinated entities', uid)
            self.coordinated.remove(uid)
