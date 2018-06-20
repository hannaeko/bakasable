import logging
import functools

import pyndn

from bakasable import (
    utils,
    entities,
    logic
)
from bakasable.entities import mngt


logger = logging.getLogger(__name__)


def load_chunks(chunks_coord):
    for coord in chunks_coord:
        mngt.load_chunk(*coord, check_coordinator=False)


def load_chunk(x, y, check_coordinator=True):
    """
    Load chunk at chunk coordinates x and y.

    If the local peer is coordinator of the chunk, try to get the chunk
    from remotes before creating it. Else request it from a remote peer.
    """
    chunk_uid = entities.MapChunk.gen_uid(
        mngt.context.game_id, x, y)
    chunk_peer = mngt.context.peer_store.get_closest_peer(chunk_uid)

    if chunk_uid in mngt.context.object_store.store:
        if check_coordinator:
            mngt.context.object_store.set_local_coordinator(chunk_uid)
        return
    if chunk_uid in mngt.pending_fetch:  # Already loading chunk
        return

    mngt.pending_fetch.add(chunk_uid)

    logger.info('Loading chunk %d (%d, %d) from peer %d',
                chunk_uid, x, y, chunk_peer.uid)
    if chunk_peer.uid == mngt.context.peer_id:
        mngt.start_recorvery(
            chunk_uid,
            failed_cb=functools.partial(mngt.create_chunk, x, y))
    else:
        mngt.send_chunk_entities_interest(chunk_peer, x, y)


def send_chunk_entities_interest(chunk_peer, x, y):
    # TODO: Bigger timeout (tree times the current one)
    name = pyndn.Name(chunk_peer.prefix) \
        .append('chunk') \
        .append(str(x)).append(str(y)) \
        .append('entities')
    logger.debug('Sending ChunkEntitiesInterest to %s', name.toUri())
    interest = pyndn.Interest(name)
    # About three times a normal timeout as two timeout may occur before
    # the chunk is created.
    interest.setInterestLifetimeMilliseconds(30000)
    mngt.context.face.expressInterest(
        interest,
        mngt.on_chunk_entities_data,
        mngt.on_chunk_entities_timeout)


@mngt.register_interest_filter('local', utils.chunk_entites_regex)
def on_chunk_entities_interest(prefix, interest, face, interest_filter_id):
    """
    Try to get the requested chunk from the local store and send it back if
    found.
    Else initiate the recorvery procedure with the chunk id before creating
    the chunk if it did not managed to find it in remote peers store.
    """
    x, y = mngt.get_x_y_tuple(interest)

    chunk_uid = entities.MapChunk.gen_uid(mngt.context.game_id, x, y)
    chunk = mngt.context.object_store.get(chunk_uid)

    logger.debug('Received ChunkEntitiesInterest for chunk %d (%d, %d)',
                 chunk_uid, x, y)
    if chunk is not None:
        mngt.context.object_store.set_local_coordinator(chunk_uid, True)
        return mngt.send_chunk_entities_data(
            interest, face, chunk)

    cb = functools.partial(mngt.send_chunk_or_create, interest, face, x, y)
    mngt.start_recorvery(
        chunk_uid,
        failed_cb=cb,  # Failure : create then send
        success_cb=cb)  # Success : fetch in store then send


def send_chunk_entities_data(interest, face, chunk):
    logger.debug('Sending ChunkEntitiesData for chunk %d (%d, %d)',
                 chunk.uid, chunk.map.x, chunk.map.y)
    chunk = entities.Chunk.serialize(chunk)

    chunk_data = pyndn.Data(interest.getName())
    chunk_data.setContent(chunk)
    face.putData(chunk_data)


def on_chunk_entities_data(interest, data):
    _, chunk = entities.Chunk.deserialize(data.getContent().toBytes())
    logger.debug('Received ChunkEntitiesData for chunk %d (%d, %d)',
                 chunk.uid, chunk.map.x, chunk.map.y)
    mngt.pending_fetch.remove(chunk.uid)
    mngt.context.object_store.add(chunk)


def on_chunk_entities_timeout(interest):
    x, y = mngt.get_x_y_tuple(interest)

    chunk_uid = entities.MapChunk.gen_uid(mngt.context.game_id, x, y)
    mngt.pending_fetch.remove(chunk_uid)
    utils.on_timeout(interest)


def send_chunk_or_create(interest, face, x, y):
    chunk = mngt.create_chunk(x, y)
    mngt.send_chunk_entities_data(interest, face, chunk)


def create_chunk(x, y):
    chunk_uid = entities.MapChunk.gen_uid(
        mngt.context.game_id, x, y)
    chunk = mngt.context.object_store.get(chunk_uid)

    if chunk_uid in mngt.pending_fetch:
        mngt.pending_fetch.remove(chunk_uid)

    # Chunk already exist in store, simply return it directly
    if chunk is not None:
        return chunk

    chunk = logic.chunk.generate_chunk(mngt.context.game_id, x, y)
    mngt.context.object_store.add(chunk)
    logger.debug('Created chunk %s', chunk)
    # TODO: assign entities to peers.
    return chunk
