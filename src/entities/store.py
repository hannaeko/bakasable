import entities.objects
import functools
import collections


class ObjectStore():
    def __init__(self, context):
        self.context = context
        self.store = {}  # {chunk_id: {entity_id: entity}}

    def add(self, obj):
        if isinstance(obj, collections.Iterable):
            for o in obj:
                self.add(o)
        else:
            self.store[obj.uid] = obj

    def get(self, uid):
        return self.store.get(uid, None)

    def get_chunk(self, x, y, **kwargs):
        chunk_uid = entities.objects.MapChunk.gen_uid(
            self.context.game_id, x, y)
        chunk = self.store.get(chunk_uid, None)
        if chunk is not None:
            return chunk

        callback = kwargs.pop('callback', None)
        if callback is None:
            return

        self.context.load_chunk(
            chunk_uid, functools.partial(callable, **kwargs))
