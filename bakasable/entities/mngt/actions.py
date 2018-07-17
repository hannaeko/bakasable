import logging

from bakasable.think import on_action
from bakasable.entities import mngt


logger = logging.getLogger(__name__)


def emit_action(type, target, sender):
    logger.debug('Action emitted %d => %d (type=%d)',
                 sender.uid, target.uid, type)
    peer = mngt.context.peer_store.get_closest_peer(target.uid)
    if peer.uid == mngt.context.peer_id:
        on_action.execute({'type': type, 'target': target, 'sender': sender})
