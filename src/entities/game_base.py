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
    GameObjects can be inherited and definition extended.
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


class Diff:
    def __init__(self, klass):
        self.klass = klass
        self.diff = {}

    def add(self, name, value):
        self.diff[name] = value

    def clear(self):
        self.diff.clear()

    def apply(self, obj):
        for key, value in self.diff.items():
            setattr(obj, key, value)

    @staticmethod
    def serialize(diff):
        res = Number.serialize(diff.klass.id)
        for index, (attr, klass) in enumerate(diff.klass.definition):
            if attr in diff.diff:
                res += Number.serialize(index)
                res += klass.serialize(diff.diff[attr])
        return res

    @staticmethod
    def deserialize(payload):
        payload, object_id = Number.deserialize(payload)
        klass = _registry[object_id]
        diff = Diff(klass)
        diff_dict = {}
        while payload:
            payload, attr_index = Number.deserialize(payload)
            attr_name, attr_type = klass.definition[attr_index]
            payload, attr_value = attr_type.deserialize(payload)
            diff_dict[attr_name] = attr_value
        diff.add(**diff_dict)
        return payload, diff

    def __repr__(self):
        res = '<%s of %s :: ' % (type(self).__name__, self.klass.__name__)
        res += '; '.join(
            '%s=%s' % (key, repr(val)) for key, val in self.diff.items())
        res += '>'
        return res


class UpdatableGameObject(GameObject):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.diff = Diff(type(self))

    def __setattr__(self, name, value):
        try:
            if name in self.attr:
                self.diff.add(name, value)
        except AttributeError:
            pass
        finally:
            object.__setattr__(self, name, value)

    def update(self, new_diff):
        new_diff.apply(self)
        self.diff.clear()
