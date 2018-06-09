import hashlib

from entities.primitives import (
    Entity,
    UID64,
    String,
    Array,
    Number
)


class Peer(Entity):
    definition = (
        ('uid', UID64),
        ('prefix', String)
    )


PeerArray = Array(Peer)


class MapChunk(Entity):
    definition = (
        ('uid', UID64),
        ('data', Array(Array(Number))),
        ('x', Number),
        ('y', Number)
    )

    @staticmethod
    gen_uid(seed, x, y):
        md5 = hashlib.md5()
        md5.update(struct.pack('!Qii', seed, x, y))
        return struct.unpack_from('!Q', md5.digest())[0]


class Chunk(Entity):
    definition = (
        ('map', MapChunk),
        ('entities', Array(GameObject))
    )
