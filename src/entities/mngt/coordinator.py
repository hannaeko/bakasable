import logging

import pyndn

from bakasable import (
    utils,
    entities,
)
from bakasable.entities import mngt


logger = logging.getLogger(__name__)


def send_coordinator_change_interest(uid):
    logger.debug('Sending CoordinatorChangeInterest for entity %d' % uid)
    name = pyndn.Name(mngt.context.broadcast_name) \
        .append('coordinator_change')\
        .append(str(uid))
    mngt.context.face.expressInterest(name, utils.on_dummy_data)


@mngt.register_interest_filter('broadcast', utils.coordinator_change_regex)
def on_coordinator_change_interest(prefix, interest, face, interest_filter_id):
    uid = int(interest.getName().get(-1).toEscapedString())
    logger.debug('Received CoordinatorChangeInterest for entity %d', uid)
    mngt.context.object_store.set_local_coordinator(uid)
