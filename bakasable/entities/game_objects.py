import struct
import hashlib
import random

import numpy as np
import pygame

from bakasable.entities.primitives import (
    Array,
    Float,
    Number,
    String,
    UID64
)
from bakasable.entities.game_base import (
    GameObject,
    UpdatableGameObject,
    DrawableGameObject
)
from bakasable.const import terrain
from bakasable.const import TILE_SIZE, SHEEP_WALKING_RANGE
from bakasable import game


class MapChunk(GameObject):
    id = 1
    override_base = True
    definition = (
        ('uid', UID64),
        ('x', Number),
        ('y', Number),
        ('data', Array(Array(Number))),
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._sprite = None

    @staticmethod
    def gen_uid(seed, x, y):
        md5 = hashlib.md5()
        md5.update(struct.pack('!Qii', seed, x, y))
        return struct.unpack_from('!Q', md5.digest())[0]

    @property
    def current_frame(self):
        if self._sprite is None:
            col_map = pygame.Surface((15, 15))
            pix = [[terrain.mapping[tile_code] for tile_code in line]
                   for line in self.data]

            pygame.surfarray.blit_array(col_map, np.array(pix))
            self._sprite = pygame.transform.scale(col_map,
                                                  (15*TILE_SIZE, 15*TILE_SIZE))

        return self._sprite


class Chunk(GameObject):
    id = 2
    override_base = True
    definition = (
        ('uid', UID64),  # For consistency and logging, same as map.uid
        ('map', MapChunk),
        ('entities', Array(GameObject)),
    )

    @property
    def uid(self):
        if self.map is not None:
            return self.map.uid

    @uid.setter
    def uid(self, value):
        pass


class Sheep(UpdatableGameObject, DrawableGameObject):
    id = 3
    sprite_name = 'sheep'
    definition = (
        ('init_x', Float),
        ('init_y', Float)
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.direction = pygame.math.Vector2(self.x, self.y)
        self.rest = 0

    def change_direction(self):
        self.direction = pygame.math.Vector2(
            random.uniform(self.x - SHEEP_WALKING_RANGE,
                           self.x + SHEEP_WALKING_RANGE),
            random.uniform(self.y - SHEEP_WALKING_RANGE,
                           self.y + SHEEP_WALKING_RANGE))


class Player(UpdatableGameObject, DrawableGameObject):
    id = 4
    definition = (
        ('pseudo', String),
    )
    sprite_name = 'player'
    animated = False
    interest_zone = 14

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.speed = pygame.math.Vector2(0, 0)
        self._additional_sprites = None

    @property
    def additional_sprites(self):
        if self._additional_sprites is None:
            self.pseudo_label = game.monospace.render(
                self.pseudo, 1, (0, 0, 0))
            self._additional_sprites = [(self.pseudo_label, 0, -20)]
        return self._additional_sprites
