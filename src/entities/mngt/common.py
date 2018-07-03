import collections

import pyndn

from bakasable.entities import mngt


interest_filters_registry = set()


def register_interest_filter(name_type, regex):
    def decorator(func):
        interest_filters_registry.add((name_type, regex, func))
        return func
    return decorator


def set_interest_filter():
    for name_type, regex, cb in interest_filters_registry:
        prefix = getattr(mngt.context, '%s_name' % name_type)
        mngt.context.face.setInterestFilter(
            pyndn.InterestFilter(prefix, regex), cb)


def add_fetch_callback(uid, callback):
    if callback is None:
        return

    mngt.fetch_callbacks.setdefault(uid, [])

    if isinstance(callback, collections.Iterable):
        mngt.fetch_callbacks[uid].extend(callback)
    else:
        mngt.fetch_callbacks[uid].append(callback)


def execute_callback(uid):
    callbacks = mngt.fetch_callbacks.pop(uid, [])
    for cb in callbacks:
        cb()


def get_peer_uid_tuple(name_or_interest):
    if isinstance(name_or_interest, pyndn.Interest):
        name = name_or_interest.getName()
    else:
        name = name_or_interest
    peer_id = int(name.get(-1).toEscapedString())
    uid = int(name.get(-2).toEscapedString())
    return peer_id, uid


def get_x_y_tuple(name_or_interest):
    if isinstance(name_or_interest, pyndn.Interest):
        name = name_or_interest.getName()
    else:
        name = name_or_interest
    x = int(name.get(-3).toEscapedString())
    y = int(name.get(-2).toEscapedString())
    return x, y
