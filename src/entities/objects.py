from entities.primitives import (
    Entity,
    UID64,
    String,
    Number,
    Option,
    Array
)
from entities.game_base import GameObject


class Peer(Entity):
    definition = (
        ('uid', UID64),
        ('prefix', String)
    )


PeerArray = Array(Peer)


class Result(Entity):
    definition = (
        ('status', Number),
        ('value', Option(GameObject))
    )
