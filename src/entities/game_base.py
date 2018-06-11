from entities.primitives import (
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

    @classmethod
    def serialize(cls, object):
        return Number.serialize(cls.id) + super().serialize(object)

    @classmethod
    def deserialize(cls, payload):
        print(payload)
        payload, object_id = Number.deserialize(payload)
        print(payload, object_id)
        return super(GameObject, _registry[object_id]).deserialize(payload)
