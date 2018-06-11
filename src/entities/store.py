import entities.objects


class ObjectStore():
    def __init__(self, game_id):
        self.game_id
        self.store = {}  # {chunk_id: {entity_id: entity}}

    def add(self, obj):
        self.store[obj.uid] = obj

    def get_chunk(self, x, y):
        chunk_uid = entities.objects.MapChunk.gen_uid(self.game_id, x, y)
        chunk = self.store.get(chunk_uid, None)
        if chunk is None:
            return
        return chunk, self.get_all_entites(x, y)

    def get_all_entites(self, x, y):
        pass
