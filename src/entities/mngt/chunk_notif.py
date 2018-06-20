import logging
import functools

import pyndn

from bakasable import (
    utils,
    entities,
)
from bakasable.entities import mngt


logger = logging.getLogger(__name__)


def send_enter_chunk_interest(entity):
    uid = entity.uid
    chunk_x, chunk_y = entity.x // 15, entity.y // 15
    chunk_uid = entities.MapChunk.gen_uid(
        mngt.context.game_id, chunk_x, chunk_y)
    chunk_peer = mngt.context.peer_store.get_closest_peer(chunk_uid)
    if chunk_peer.uid == mngt.context.peer_id:
        mngt.emit_enter_chunk_update(chunk_x, chunk_y, entity)
        return
    name = pyndn.Name(chunk_peer.prefix) \
        .append('chunk') \
        .append(str(chunk_x)) \
        .append(str(chunk_y)) \
        .append('enter') \
        .append(str(uid))
    logger.debug('Sending EnterChunkInterest for entity %d '
                 'and chunk %d (%d, %d)',
                 uid, chunk_uid, chunk_x, chunk_y)

    mngt.context.face.expressInterest(name, utils.on_dummy_data)


def on_enter_chunk_interest(prefix, interest, face, interest_filter_id):
    uid = int(interest.getName().get(-1).toEscapedString())
    x, y = mngt.get_x_y_tuple(interest.getName().getPrefix(-1))
    logger.debug('Received EnterChunkInterest for entity %d '
                 'and chunk (%d, %d)',
                 uid, x, y)
    mngt.load_entity(
        uid, functools.partial(mngt.emit_enter_chunk_update, x, y, uid))
    mngt.load_chunk(x, y)
