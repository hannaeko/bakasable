import random

import noise

from bakasable import (
    entities,
)
import bakasable.const.terrain


def generate_chunk_map(seed, chunk_x, chunk_y):
    new_seed = (seed / (1 << 56))  # bring the seed between 0 and 256
    freq = 64 * 8
    data = []

    for x in range(chunk_x * 15, (chunk_x + 1) * 15):
        line = []
        for y in range(chunk_y * 15, (chunk_y + 1) * 15):
            threshold = (noise.snoise3(x / freq, y / freq, new_seed, 8) + 1) / 2
            if threshold < 0.3:
                tile = bakasable.const.terrain.MOUNTAIN
            elif threshold < 0.6:
                tile = bakasable.const.terrain.GRASS
            else:
                tile = bakasable.const.terrain.WATER
            line.append(tile)
        data.append(line)

    return entities.MapChunk(
        x=chunk_x, y=chunk_y,
        data=data,
        uid=entities.MapChunk.gen_uid(seed, chunk_x, chunk_y))


def generate_chunk_entities(seed, x, y):
    return [
        entities.Sheep(
            x=(x*15+8),
            init_x=(x*15+8),
            y=(y*15+8),
            init_y=(y*15+8),
            uid=random.getrandbits(64))
        for i in range(5)
        ]


def generate_chunk(seed, x, y):
    return entities.Chunk(
        map=generate_chunk_map(seed, x, y),
        entities=generate_chunk_entities(seed, x, y))


def get_chunk_range(top_left_x, top_left_y, bottom_right_x, bottom_right_y):
    chunks = set()
    x_range = range(int((top_left_x) // 15),
                    int((bottom_right_x) // 15 + 1))
    y_range = range(int((top_left_y) // 15),
                    int((bottom_right_y) // 15 + 1))

    for chunk_x in x_range:
        for chunk_y in y_range:
            chunks.add((chunk_x, chunk_y))
    return chunks
