import collections

import entities


class ObjectStore():
    def __init__(self, context):
        self.context = context
        self.store = {}  # {chunk_id: {entity_id: entity}}
        self.coordinated = set()

    def add(self, obj, coordinator=False):
        if isinstance(obj, collections.Iterable):
            for o in obj:
                self.add(o, coordinator=coordinator)
        elif isinstance(obj, entities.Chunk):
            self.add(obj.map, coordinator=coordinator)
            self.add(obj.entities)
        else:
            self.store[obj.uid] = obj
            if coordinator:
                self.coordinated.add(obj.uid)

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
        elif uid in self.coordinated:
            self.coordinated.remove(uid)
