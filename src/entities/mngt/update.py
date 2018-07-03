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


def subscribe_updates(chunks_coord, player_watch):
    new_chunks = chunks_coord - mngt.watched_chunks

    mngt.watched_chunks = chunks_coord
    mngt.player_watch = player_watch

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
    mngt.send_chunk_update_interest(
        chunk.map.x, chunk.map.y, chunk.map.uid)
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


def emit_entity_state_change(entity):
    if not entity.diff:
        return

    update = entities.Update(type=const.status_code.STATE_CHANGE,
                             value=entity.diff)
    send_entity_update_data(entity.uid, entity.version, update)


def emit_entity_catch_up(entity, version):
    logger.trace('Emit catch up for entity %d [%d -> %d]',
                 entity.uid, version, entity.version)
    diff = entity.diff.compute_diff_from(version)
    if diff:
        update = entities.Update(type=const.status_code.STATE_CHANGE,
                                 value=diff)
    else:
        update = entities.Update(type=const.status_code.FULL_STATE,
                                 value=entities.Diff(entity))
    send_entity_update_data(entity.uid, version, update)


# EntityUpdateInterest

def send_entity_update_interest(uid, interest=None):
    entity = mngt.context.object_store.get(uid)

    peer = mngt.context.peer_store.get_closest_peer(uid)
    chunk_coord = (entity.x // 15, entity.y // 15)

    # No need to subscribe for updates if the local peer is coordinator
    if peer.uid == mngt.context.peer_id:
        # TODO: active check when coordinator leave the game
        # (prevent entity freeze)
        # mngt.context.object_store.set_local_coordinator(entity.uid, True)
        logger.debug('Skipping send EntityUpdateInterest for entity %s: '
                     'entity coordinated by local peer',
                     uid)
        return

    # Entity not watch anymore
    if chunk_coord not in mngt.watched_chunks:
        logger.debug('Skipping send EntityUpdateInterest for entity %s: '
                     'chunk not watched, chunk=(%d, %d) watched_chunks=%s',
                     uid, entity.x // 15, entity.y // 15, mngt.watched_chunks)

        entity.active = False
        return

    entity.active = True

    name = pyndn.Name(peer.prefix) \
        .append('entity') \
        .append(str(uid)) \
        .append('updates') \
        .append(str(entity.version))

    if chunk_coord in mngt.player_watch:
        name.append('touch')

    logger.trace('Sending EntityUpdateInterest for entity %d to %d, %s',
                 uid, peer.uid, name)
    mngt.context.face.expressInterest(
        name,
        mngt.on_entity_update_data,
        functools.partial(mngt.send_entity_update_interest, uid))


@mngt.register_interest_filter('local', utils.entity_update_regex)
def on_entity_update_interest(prefix, interest, face, interest_filter_id):
    touch = False
    if interest.getName().get(-1).toEscapedString() == 'touch':
        touch = True
    uid = int(interest.getName().get(-3 - touch).toEscapedString())
    version = int(interest.getName().get(-1 - touch).toEscapedString())

    logger.trace(
        'Received EntityUpdateInterest for entity %d  with version %d',
        uid, version)

    entity = mngt.context.object_store.get(uid)
    if entity is not None:
        logger.trace('Found entity in local store with version %d',
                     entity.version)
        if touch:
            entity.touch()
        # NOTE: remote version > local -> coordinator trust so send full state
        if version != entity.version:
            mngt.emit_entity_catch_up(entity, version)
        else:
            logger.trace('Entity %d update to date in remote store',
                         entity.uid)
    else:
        mngt.load_entity(uid)


def send_entity_update_data(uid, version, update):
    logger.trace('Sending EntityUpdateData for entity %d %s', uid, update)

    name = pyndn.Name(mngt.context.local_name) \
        .append('entity') \
        .append(str(uid)) \
        .append('updates') \
        .append(str(version)) \
        .append('touch')

    entity_update_data = pyndn.Data(name)
    entity_update_data.setContent(entities.Update.serialize(update))
    mngt.context.face.putData(entity_update_data)


def on_entity_update_data(interest, data):
    uid = int(data.getName().get(-4).toEscapedString())
    logger.trace('Update received for entity %d', uid)
    entity = mngt.context.object_store.get(uid, expend_chunk=False)
    _, update = entities.Update.deserialize(data.getContent().toBytes())
    if update.type in (const.status_code.STATE_CHANGE,
                       const.status_code.FULL_STATE):
        entity.update(update.value)
    mngt.send_entity_update_interest(uid)


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

    if (chunk_x, chunk_y) in mngt.player_watch:
        name.append('touch')

    logger.debug('Sending ChunkUpdateInterest for chunk %d (%d, %d) to %d',
                 uid, chunk_x, chunk_y, peer.uid)

    mngt.context.face.expressInterest(
        name,
        mngt.on_chunk_update_data,
        functools.partial(
            mngt.send_chunk_update_interest, chunk_x, chunk_y, uid))


@mngt.register_interest_filter('local', utils.chunk_update_regex)
def on_chunk_update_interest(prefix, interest, face, interest_filter_id):
    touch = False
    name = interest.getName()
    if interest.getName().get(-1).toEscapedString() == 'touch':
        touch = True
        name = name.getPrefix(-1)

    x, y = mngt.get_x_y_tuple(name)
    logger.debug('Received ChunkUpdateInterest for chunk (%d, %d)', x, y)
    chunk = mngt.context.object_store.get_chunk(x, y)

    if chunk is not None and touch:
        logger.debug('Chunk touched')
        chunk.touch()
    elif not chunk:
        mngt.load_chunk(x, y)


def send_chunk_update_data(chunk_x, chunk_y, update):
    logger.debug('Sending ChunkUpdateData for chunk (%d, %d): %s',
                 chunk_x, chunk_y, update)
    name = pyndn.Name(mngt.context.local_name) \
        .append('chunk') \
        .append(str(chunk_x)) \
        .append(str(chunk_y)) \
        .append('updates') \
        .append('touch')

    chunk_update_data = pyndn.Data(name)
    chunk_update_data.setContent(entities.Result.serialize(update))
    mngt.context.face.putData(chunk_update_data)


def on_chunk_update_data(interest, data):
    x, y = mngt.get_x_y_tuple(data.getName().getPrefix(-1))
    uid = entities.MapChunk.gen_uid(mngt.context.game_id, x, y)

    _, update = entities.Result.deserialize(data.getContent().toBytes())
    logger.debug('Update received for chunk (%d, %d): %s', x, y, update)
    if update.status == const.status_code.ENTER_CHUNK:
        mngt.context.object_store.add(update.value)
        mngt.send_entity_update_interest(update.value.uid)

    mngt.send_chunk_update_interest(x, y, uid)
