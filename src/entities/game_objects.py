from entities.primitives import (
    String,
)
from entities.game_base import GameObject


class Sheep(GameObject):
    id = 1
    definition = (
        ('plouf', String),
    )
