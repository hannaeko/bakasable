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
    chunk_x, chunk_y = int(entity.x // 15), int(entity.y // 15)
    chunk_uid = entities.MapChunk.gen_uid(
        mngt.context.game_id, chunk_x, chunk_y)
    chunk_peer = mngt.context.peer_store.get_closest_peer(chunk_uid)
    if chunk_peer.uid == mngt.context.peer_id:
        # NOTE: Workaround to send update after coordinator transfert
        # TODO: Maybe need to be more robust
        mngt.load_chunk(
            chunk_x, chunk_y, callback=functools.partial(
                mngt.emit_enter_chunk_update, chunk_x, chunk_y, entity))
        return
    name = pyndn.Name(chunk_peer.prefix) \
        .append('chunk') \
        .append(str(chunk_x)) \
        .append(str(chunk_y)) \
        .append('enter') \
        .append(str(uid))
    logger.debug('Sending EnterChunkInterest for entity %d '
                 'and chunk %d (%d, %d), %s',
                 uid, chunk_uid, chunk_x, chunk_y, entity)

    mngt.context.face.expressInterest(name, utils.on_dummy_data)


@mngt.register_interest_filter('local', utils.enter_chunk_regex)
def on_enter_chunk_interest(prefix, interest, face, interest_filter_id):
    uid = int(interest.getName().get(-1).toEscapedString())
    x, y = mngt.get_x_y_tuple(interest.getName().getPrefix(-1))
    logger.debug('Received EnterChunkInterest for entity %d '
                 'and chunk (%d, %d)',
                 uid, x, y)
    mngt.load_entity(
        uid, (functools.partial(mngt.emit_enter_chunk_update, x, y, uid),
              functools.partial(mngt.send_entity_update_interest, uid)))
    mngt.load_chunk(x, y)
