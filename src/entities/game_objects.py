import struct
import hashlib

from entities.primitives import (
    String,
    UID64,
    Number,
    Array
)
from entities.game_base import GameObject


class MapChunk(GameObject):
    id = 1
    definition = (
        ('data', Array(Array(Number)))
    )

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
