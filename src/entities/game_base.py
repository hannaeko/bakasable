import pygame
import os

from bakasable import game
from bakasable.utils import asset_path
from bakasable.entities.primitives import (
    String,
    Number,
    Entity,
    UID64
)


_registry = {}


class GameObjectType(type):
    """
    Metaclass for class GameObject.
    Merge 'definition' attributes from base classes and register the game
    object in registry.
    """
    def __new__(cls, name, bases, namespace, **kwargs):
        if 'definition' not in namespace:
            namespace['definition'] = ()
        if not namespace.get('override_base', False):
            for klass in bases:
                namespace['definition'] += getattr(klass, 'definition', ())

        res = super().__new__(cls, name, bases, namespace)
        _registry[res.id] = res
        return res


class GameObject(Entity, metaclass=GameObjectType):
    """
    Game object, must have a unique non-zero id attribute.
    By default has two attributes, x and y for position.
    GameObjects can be inherited and defintion extended.
    """
    id = 0
    definition = (
        ('x', Number),
        ('y', Number),
        ('uid', UID64)
    )
    sprite = None
    animated = False
    interest_zone = 0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.sprite:
            self._sprite = game.Sprite(self.sprite, self.animated)

    @classmethod
    def serialize(cls, object):
        return Number.serialize(cls.id) + super().serialize(object)

    @classmethod
    def deserialize(cls, payload):
        payload, object_id = Number.deserialize(payload)
        return super(GameObject, _registry[object_id]).deserialize(payload)

    def get_sprite(self):
        if self.sprite:
            return self._sprite.current_frame
