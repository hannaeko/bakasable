import logging
import functools

import pyndn

from bakasable import (
    const,
    entities,
    utils,
)
from bakasable.entities import mngt


logger = logging.getLogger(__name__)


def subscribe_updates(chunks_coord):
    new_chunks = chunks_coord - mngt.watched_chunks

    mngt.watched_chunks = chunks_coord

    for chunk_coord in new_chunks:
        chunk = mngt.context.object_store.get_chunk(*chunk_coord)
        if chunk is not None:
            mngt.subscribe_updates_single_chunk(chunk)
        else:
            mngt.watched_chunks.remove(chunk_coord)


def subscribe_updates_single_chunk(chunk):
    """
    Subscribe to updates of all entity in chunk.
    """
    mngt.send_chunk_update_interest(chunk.map.x, chunk.map.y, chunk.map.uid)
    for entity in chunk.entities:
        mngt.send_entity_update_interest(entity.uid)


def emit_enter_chunk_update(chunk_x, chunk_y, entity_or_uid):
    if isinstance(entity_or_uid, int):
        entity = mngt.context.object_store.get(entity_or_uid)
    else:
        entity = entity_or_uid
    update = entities.Result(
        status=const.status_code.ENTER_CHUNK, value=entity)
    mngt.send_chunk_update_data(chunk_x, chunk_y, update)


# EntityUpdateInterest

def send_entity_update_interest(uid, interest=None):
    entity = mngt.context.object_store.get(uid)
    # Entity not watch anymore
    if (entity.x // 15, entity.y // 15) not in mngt.watched_chunks:
        return

    peer = mngt.context.peer_store.get_closest_peer(uid)

    # No need to subscribe for updates if the local peer is coordinator
    if peer.uid == mngt.context.peer_id:
        return

    name = pyndn.Name(peer.prefix) \
        .append('entity') \
        .append(str(uid)) \
        .append('updates')

    logger.debug('Sending EntityUpdateInterest for entity %d with name %s',
                 uid, name.toUri())

    mngt.context.face.expressInterest(
        name,
        mngt.on_entity_update_data,
        functools.partial(
            mngt.send_entity_update_interest, uid))


@mngt.register_interest_filter('local', utils.entity_update_regex)
def on_entity_update_interest(prefix, interest, face, interest_filter_id):
    uid = int(interest.getName().get(-2).toEscapedString())
    logger.debug('Received EntityUpdateInterest for entity %d', uid)
    mngt.load_entity(uid)


def send_entity_update_data(uid, update):
    logger.debug('Sending EntityUpdateData for entity %d %s', uid, update)

    name = pyndn.Name(mngt.context.local_name) \
        .append('entity') \
        .append(str(uid)) \
        .append('updates')

    entity_update_data = pyndn.Data(name)
    entity_update_data.setContent(entities.Update.serialize(update))
    mngt.context.face.putData(entity_update_data)


def on_entity_update_data(interest, data):
    uid = int(interest.getName().get(-2).toEscapedString())
    logger.debug('Update received for entity %d', uid)


# ChunkUpdateInterest

def send_chunk_update_interest(chunk_x, chunk_y, uid, interest=None):
    # Chunk not watched anymore, stop here
    if (chunk_x, chunk_y) not in mngt.watched_chunks:
        return

    # Neep to check peer actively to be aware of coordinator changes
    # TODO: See if possible to use leave event to be more lazy
    peer = mngt.context.peer_store.get_closest_peer(uid)

    # No need to subscribe for updates if the local peer is coordinator
    if peer.uid == mngt.context.peer_id:
        # mngt.watched_chunks.remove((chunk_x, chunk_y))
        return

    name = pyndn.Name(peer.prefix) \
        .append('chunk') \
        .append(str(chunk_x)) \
        .append(str(chunk_y)) \
        .append('updates')

    logger.debug('Sending ChunkUpdateInterest for chunk %d (%d, %d) '
                 'with name %s',
                 uid, chunk_x, chunk_y, name.toUri())

    mngt.context.face.expressInterest(
        name,
        mngt.on_chunk_update_data,
        functools.partial(
            mngt.send_chunk_update_interest, chunk_x, chunk_y, uid))


@mngt.register_interest_filter('local', utils.chunk_update_regex)
def on_chunk_update_interest(prefix, interest, face, interest_filter_id):
    x, y = mngt.get_x_y_tuple(interest)
    logger.debug('Received ChunkUpdateInterest for chunk (%d, %d)', x, y)
    mngt.load_chunk(x, y)


def send_chunk_update_data(chunk_x, chunk_y, update):
    logger.debug('Sending ChunkUpdateData for chunk (%d, %d)',
                 chunk_x, chunk_y)
    name = pyndn.Name(mngt.context.local_name) \
        .append('chunk') \
        .append(str(chunk_x)) \
        .append(str(chunk_y)) \
        .append('updates')

    chunk_update_data = pyndn.Data(name)
    chunk_update_data.setContent(entities.Result.serialize(update))
    mngt.context.face.putData(chunk_update_data)


def on_chunk_update_data(interest, data):
    x, y = mngt.get_x_y_tuple(interest)
    logger.debug('Update received for chunk (%d, %d)', x, y)
