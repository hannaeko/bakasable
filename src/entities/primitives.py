import struct


class String(str):
    """
    List of bytes of unknown length. Ends with \x00
    """
    @staticmethod
    def deserialize(payload):
        res = b''
        while len(payload) and payload[0] != 0x00:
            res += struct.unpack_from('s', payload)[0]
            payload = payload[1:]
        return payload[1:], res.decode('utf8')

    @staticmethod
    def serialize(my_str):
        return my_str.encode('utf8') + b'\x00'


class Number(int):
    """
    Generic class for numbers, encoded in big endian.
    Default to 4 bytes signed int.
    """
    my_struct = struct.Struct('!i')

    @classmethod
    def deserialize(cls, payload):
        res = cls.my_struct.unpack_from(payload)[0]
        return payload[cls.my_struct.size:], res

    @classmethod
    def serialize(cls, my_int):
        return cls.my_struct.pack(my_int)


class UID64(int):
    """
    Unsigned int of 8 bytes (big endian).
    """
    @staticmethod
    def deserialize(payload):
        res = struct.unpack_from('!Q', payload)[0]
        return payload[8:], res

    @staticmethod
    def serialize(uid):
        return struct.pack('!Q', uid)


class _Array(list):
    """
    Represent a list where all elements have the same type.
    Do not use it derectly but call Array(MyClass) instead.
    """
    my_type = None

    @classmethod
    def deserialize(cls, payload):
        res = list()
        length = struct.unpack_from('!I', payload)[0]
        payload = payload[4:]
        for i in range(0, length):
            payload, element = cls.my_type.deserialize(payload)
            res.append(element)
        return payload, res

    @classmethod
    def serialize(cls, my_list):
        res = b''
        my_len = 0
        for element in my_list:
            if hasattr(element, 'serialize'):
                res += element.serialize(element)
            else:
                res += cls.my_type.serialize(element)
            my_len += 1
        return struct.pack('!I', my_len) + res


def Array(klass):
    """
    An array represent a list of element where all elements have the same type
    (klass).
    If the elements have a method 'serialize', it will be used instead of the
    one of the given class for the serialization.
    For the deserialization, the deserialize method of 'klass' will be used.
    """
    return type('%sArray' % klass.__name__, (_Array,), {'my_type': klass})


class _Option:
    """
    Optional type.
    Should not be used directly, call Option(MyClass) instead.
    """
    my_type = None

    @classmethod
    def deserialize(cls, payload):
        if payload[0] == 0x00:
            return payload[1:], None
        else:
            return cls.my_type.deserialize(payload[1:])

    @classmethod
    def serialize(cls, my_option):
        if my_option is None:
            return b'\x00'
        else:
            if hasattr(my_option, 'deserialize'):
                return b'\x01' + my_option.serialize(my_option)
            else:
                return b'\x01' + cls.my_type.serialize(my_option)


def Option(klass):
    """
    The value of an Option field can be either an object or None.
    The class passed in argument will be used for serialization and
    deserialization of non None value.
    If the value has a method 'serialize', it will be used instead of the
    one of the given class.
    """
    return type('OptionOf%s' % klass.__name__, (_Option,), {'my_type': klass})


class Entity:
    """
    Composition of Entity or primitives.
    The definition is a list of tuple with the name of the attibute first and
    the type of the attibute in second.
    """
    definition = ()

    def __init__(self, **kwargs):
        self.attr = list(zip(*self.definition))[0]
        for key in self.attr:
            setattr(self, key, kwargs.get(key))

    @classmethod
    def serialize(cls, entity):
        res = bytes()
        for attr, klass in cls.definition:
            res += klass.serialize(getattr(entity, attr))
        return res

    @classmethod
    def deserialize(cls, payload):
        attr_dict = {}
        for attr, klass in cls.definition:
            payload, attr_dict[attr] = klass.deserialize(payload)
        return payload, cls(**attr_dict)

    def __repr__(self):
        res = '<%s ' % type(self).__name__
        res += '; '.join(
            '%s=%s' % (key, repr(getattr(self, key))) for key in self.attr)
        res += '>'
        return res
