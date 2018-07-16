import os
import copy
import inspect
from collections import deque
from functools import reduce

import pygame

from bakasable.entities import mngt
from bakasable import game
from bakasable import const
from bakasable.utils import (
    asset_path,
    get_timestamp
)
from bakasable.entities.primitives import (
    String,
    Number,
    Float,
    UID64,
    Entity,
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
        ('x', Float),
        ('y', Float),
        ('uid', UID64),
    )

    interest_zone = 0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.active = False
        self.touch()

    def touch(self):
        self.freshness = get_timestamp()

    @property
    def is_fresh(self):
        return (self.x // 15, self.y // 15) in mngt.player_watch or \
               self.freshness + const.FRESH_TIMEOUT > get_timestamp()

    @classmethod
    def serialize(cls, object):
        return Number.serialize(cls.id) + super().serialize(object)

    @classmethod
    def deserialize(cls, payload):
        payload, object_id = Number.deserialize(payload)
        return super(GameObject, _registry[object_id]).deserialize(payload)


class Diff:
    def __init__(self, obj):
        self.diff = {}

        if inspect.isclass(obj):
            self.klass = obj
        else:
            self.klass = type(obj)
            for attr in obj.attr:
                self.diff[attr] = getattr(obj, attr)
            del self.diff['uid']

        self.archives = deque(maxlen=50)

    def add(self, name, value):
        self.diff[name] = value
        self.diff['timestamp'] = get_timestamp()

    def clear(self):
        if len(self.diff):
            self.archives.append(copy.deepcopy(self.diff))
            self.diff.clear()

    def compute_diff_from(self, version):
        if self.archives and self.archives[0]['version'] <= version:
            tot_update = {}
            for update in filter(lambda u: u['version'] > version,
                                 self.archives):
                tot_update.update(update)
            tot_diff = Diff(self.klass)
            tot_diff.diff = tot_update

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
        while payload:
            payload, attr_index = Number.deserialize(payload)
            attr_name, attr_type = klass.definition[attr_index]
            payload, attr_value = attr_type.deserialize(payload)
            diff.diff[attr_name] = attr_value
        return payload, diff

    def __len__(self):
        return len(self.diff)

    def __repr__(self):
        res = '<%s of %s :: ' % (type(self).__name__, self.klass.__name__)
        res += '; '.join(
            '%s=%s' % (key, repr(val)) for key, val in self.diff.items())
        res += '>'
        return res


class UpdatableGameObject(GameObject):
    definition = (
        ('version', Number()),
        ('timestamp', UID64()),
    )

    def __init__(self, **kwargs):
        kwargs.setdefault('timestamp', get_timestamp())
        kwargs.setdefault('version', 1)

        super().__init__(**kwargs)
        self.diff = Diff(type(self))

    def __setattr__(self, name, value):
        try:
            if name in self.attr:
                if not self.diff:
                    self.diff.add('version', self.version + 1)
                self.diff.add(name, value)
            else:
                object.__setattr__(self, name, value)
        except AttributeError:
            object.__setattr__(self, name, value)

    def update(self, new_diff=None):
        if new_diff is None:
            new_diff = self.diff
        try:
            if new_diff.diff['version'] > self.version:
                for key, value in new_diff.diff.items():
                    object.__setattr__(self, key, value)
                self.diff.clear()
        except KeyError:
            pass

    def chunk_changed(self):
        if 'x' in self.diff.diff or 'y' in self.diff.diff:
            new_x = self.diff.diff.get('x', self.x)
            new_y = self.diff.diff.get('y', self.y)
            return new_x // 15 != self.x // 15 or new_y // 15 != self.y // 15
        return False


class FrameDef(Entity):
    definition = (
        ('indice', Number),
    )


class DrawableGameObject(GameObject):
    # definition = (
    #     ('frame_def', FrameDef),
    # )

    sprite_name = None
    animated = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._sprite = None

    @property
    def current_frame(self):
        return self.sprite.current_frame

    @property
    def sprite(self):
        if self._sprite is None:
            self._sprite = game.Sprite(self.sprite_name, self.animated)
        return self._sprite
