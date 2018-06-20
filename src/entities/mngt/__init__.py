import logging

import pyndn

from bakasable import utils
from bakasable.entities.mngt.chunk import *
from bakasable.entities.mngt.chunk_notif import *
from bakasable.entities.mngt.entity import *
from bakasable.entities.mngt.recorvery import *
from bakasable.entities.mngt.update import *


logger = logging.getLogger(__name__)

recorvering_registry = {}
pending_fetch = set()
watched_chunks = set()
fetch_callbacks = {}
context = None


def start(ctx):
    global context
    context = ctx

    context.face.registerPrefix(
        pyndn.Name(context.local_name),
        None,
        utils.on_registration_failed,
        utils.on_registration_success)

    context.face.registerPrefix(
        pyndn.Name(context.broadcast_name),
        None,
        utils.on_registration_failed,
        utils.on_registration_success)

    # ChunkEntitiesInterest
    context.face.setInterestFilter(
        pyndn.InterestFilter(
            context.local_name, utils.chunk_entites_regex),
        on_chunk_entities_interest)

    # FindCoordinatorInterest
    context.face.setInterestFilter(
        pyndn.InterestFilter(
            context.broadcast_name, utils.find_coordinator_regex),
        on_find_coordinator_interest)

    # FindEntityInterest
    context.face.setInterestFilter(
        pyndn.InterestFilter(
            context.broadcast_name, utils.find_entity_regex),
        on_find_entity_interest)

    # EntityFoundInterest
    context.face.setInterestFilter(
        pyndn.InterestFilter(
            context.local_name, utils.entity_found_regex),
        on_entity_found_interest)

    # FetchEntityInterest
    context.face.setInterestFilter(
        pyndn.InterestFilter(
            context.local_name, utils.entity_fetch_regex),
        on_fetch_entity_interest)

    # EnterChunkInterest
    context.face.setInterestFilter(
        pyndn.InterestFilter(
            context.local_name, utils.enter_chunk_regex),
        on_enter_chunk_interest)

    # EntityUpdateInterest
    context.face.setInterestFilter(
        pyndn.InterestFilter(
            context.local_name, utils.entity_update_regex),
        on_entity_update_interest)

    # ChunkUpdateInterest
    context.face.setInterestFilter(
        pyndn.InterestFilter(
            context.local_name, utils.chunk_update_regex),
        on_chunk_update_interest)


def add_fetch_callback(uid, callback):
    if callback is None:
        return

    fetch_callbacks.setdefault(uid, [])
    fetch_callbacks[uid].append(callback)


def execute_callback(uid):
    callbacks = fetch_callbacks.pop(uid, [])
    for cb in callbacks:
        cb()


def get_peer_uid_tuple(interest):
    peer_id = int(interest.getName().get(-1).toEscapedString())
    uid = int(interest.getName().get(-2).toEscapedString())
    return peer_id, uid


def get_x_y_tuple(name_or_interest):
    if isinstance(name_or_interest, pyndn.Interest):
        name = name_or_interest.getName()
    else:
        name = name_or_interest
    x = int(name.get(-3).toEscapedString())
    y = int(name.get(-2).toEscapedString())
    return x, y
