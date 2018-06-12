import random

import noise


def generate_chunk_map(seed, x, y):
    seed = (seed / (1 << 56))  # bring the seed between 0 and 256
    freq = 64 * 8
    data = []

    for x in range(15):
        data.append([])
        for y in range(15):
            threshold = (noise.snoise3(x / freq, y / freq, seed, 8) + 1) / 2
            if threshold < 0.3:
                tile = const.terrain.MOUNTAIN
            elif threshold < 0.6:
                tile = const.terrain.GRASS
            else:
                tile = const.terrain.WATER
            data[x].append(tile)

    return entities.MapChunk(
        x=x, y=y, data=data, uid=entities.MapChunk.gen_uid(seed, x, y))


def generate_chunk_entities(seed, x, y):
    return (entities.Sheep(x=(x*15+8), y=(y*15+8), uid=random.getrandbits(64)), )


def generate_chunk(seed, x, y):
    return entities.Chunk(
        map=generate_chunk_map(),
        entities=generate_chunk_entities())
