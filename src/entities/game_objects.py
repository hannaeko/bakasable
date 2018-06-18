import struct
import hashlib

import numpy as np
import pygame

from bakasable.entities.primitives import (
    String,
    UID64,
    Number,
    Array
)
from bakasable.entities.game_base import GameObject
from bakasable.const import terrain
from bakasable.const import TILE_SIZE


class MapChunk(GameObject):
    id = 1
    definition = (
        ('data', Array(Array(Number))),
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        col_map = pygame.Surface((15, 15))
        pix = [[terrain.mapping[tile_code] for tile_code in line]
               for line in self.data]

        pygame.surfarray.blit_array(col_map, np.array(pix))
        self.sprite = pygame.transform.scale(col_map,
                                             (15*TILE_SIZE, 15*TILE_SIZE))

    @staticmethod
    def gen_uid(seed, x, y):
        md5 = hashlib.md5()
        md5.update(struct.pack('!Qii', seed, x, y))
        return struct.unpack_from('!Q', md5.digest())[0]


class Chunk(GameObject):
    id = 2
    override_base = True
    definition = (
        ('uid', UID64),  # For consistency and logging, same as map.uid
        ('map', MapChunk),
        ('entities', Array(GameObject))
    )

    @property
    def uid(self):
        if self.map is not None:
            return self.map.uid

    @uid.setter
    def uid(self, value):
        pass


class Sheep(GameObject):
    id = 3
    definition = (
        ('plouf', String),
    )


class Player(GameObject):
    id = 4
    definition = (
        ('pseudo', String),
    )
    sprite = 'player'
    animated = True
    interest_zone = 14
