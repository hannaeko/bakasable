import logging

import pyndn

from bakasable.think import on_action
from bakasable.entities import mngt
from bakasable import utils


logger = logging.getLogger(__name__)


def emit_action(type, target, sender):
    logger.debug('Emit action %d => %d (type=%d)',
                 sender.uid, target.uid, type)
    peer = mngt.context.peer_store.get_closest_peer(target.uid)
    if peer.uid == mngt.context.peer_id:
        on_action.execute({'type': type, 'target': target, 'sender': sender})
    else:
        mngt.send_action_interest(peer, type, target, sender)


def send_action_interest(peer, type, target, sender):
    name = pyndn.Name(peer.prefix) \
        .append('entity') \
        .append(str(target.uid)) \
        .append('action') \
        .append(str(sender.uid)) \
        .append(str(type))
    logger.debug('Sending ActionInterest to=%d, from=%d, type=%d',
                 target.uid, sender.uid, type)
    mngt.context.face.expressInterest(name, utils.on_dummy_data)


@mngt.register_interest_filter('local', utils.action_interest_regex)
def on_action_interest(prefix, interest, face, interest_filter_id):
    logger.debug('Received ActionInterest')
