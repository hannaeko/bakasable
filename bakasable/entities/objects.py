from bakasable.entities.primitives import (
    Entity,
    UID64,
    String,
    Number,
    Option,
    Array
)
from bakasable.entities.game_base import GameObject, Diff


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


class Update(Entity):
    definition = (
        ('type', Number),
        ('value', Option(Diff))
    )
