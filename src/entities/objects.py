from entities.primitives import (
    Entity,
    UID64,
    String,
    Array
)


class Peer(Entity):
    definition = (
        ('uid', UID64),
        ('prefix', String)
    )


PeerArray = Array(Peer)
