import logging

import pyndn

from bakasable import (
    utils,
    entities,
)
from bakasable.entities import mngt


logger = logging.getLogger(__name__)


def start_recorvery(uid, success_cb=None, failed_cb=None):
    logger.debug('Starting recorvery for entity %d', uid)

    # Alone in game, abort recorvery
    if len(mngt.context.peer_store) == 1:
        failed_cb()
        return
    recorvery_running = True
    if uid not in mngt.recorvering_registry:
        mngt.recorvering_registry[uid] = {
            'success': [],
            'failed': [],
            'peers': []
        }
        recorvery_running = False

    if success_cb:
        mngt.recorvering_registry[uid]['success'].append(success_cb)
    if failed_cb:
        mngt.recorvering_registry[uid]['failed'].append(failed_cb)

    if not recorvery_running:
        mngt.send_find_coordinator_interest(uid)


# FindCoordinatorInterest

def send_find_coordinator_interest(uid):
    name = pyndn.Name(mngt.context.broadcast_name) \
        .append('coordinator') \
        .append(str(uid)) \
        .append(str(mngt.context.peer_id))
    logger.debug('Sending FindCoordinatorInterest to %s', name.toUri())
    mngt.context.face.expressInterest(
        name,
        mngt.on_find_coordinator_data,
        mngt.on_find_coordinator_timeout)


@mngt.register_interest_filter('broadcast', utils.find_coordinator_regex)
def on_find_coordinator_interest(prefix, interest, face, interest_filter_id):
    peer_id, uid = mngt.get_peer_uid_tuple(interest)
    logger.debug('Received FindCoordinatorInterest for entity %d from peer %d',
                 uid, peer_id)

    if not mngt.context.object_store.is_local_coordinator(uid):
        return
    entity = mngt.context.object_store.get(uid)

    # TODO: End pending update interests with CoordinatorChangedData

    mngt.context.object_store.set_local_coordinator(uid, False)
    mngt.send_find_coordinator_data(interest, face, entity)


def send_find_coordinator_data(interest, face, entity):
    logger.debug('Sending FindCoordinatorData for entity %d', entity.uid)

    final_object = entity.serialize(entity)

    find_coordinator_data = pyndn.Data(interest.getName())
    find_coordinator_data.setContent(final_object)
    face.putData(find_coordinator_data)


def on_find_coordinator_data(interest, data):
    entity = entities.GameObject.deserialize(data.getContent().toBytes())
    mngt.context.object_store.add(entity)

    peer_id, uid = mngt.get_peer_uid_tuple(interest)
    logger.debug('Successfuly found coordinator for entity %d', uid)

    recorvery_obj = mngt.recorvering_registry[uid]
    del mngt.recorvering_registry[uid]

    for success_cb in recorvery_obj['success']:
        success_cb()
    mngt.execute_callback(uid)


def on_find_coordinator_timeout(interest):
    peer_id, uid = mngt.get_peer_uid_tuple(interest)

    logger.debug('Failed to find coordinator for entity %d', uid)
    mngt.send_find_entity_interest(uid)


# FindEntityInterest

def send_find_entity_interest(uid):
    logger.debug('Sending FindEntityInterest for entity %d', uid)
    name = pyndn.Name(mngt.context.broadcast_name) \
        .append('entity') \
        .append(str(uid)) \
        .append(str(mngt.context.peer_id))
    mngt.context.face.expressInterest(
        name,
        utils.on_dummy_data,
        mngt.on_find_entity_timeout)


@mngt.register_interest_filter('broadcast', utils.find_entity_regex)
def on_find_entity_interest(prefix, interest, face, interest_filter_id):
    peer_id, uid = mngt.get_peer_uid_tuple(interest)
    logger.debug('Received FindEntityInterest for entity %d from peer %d',
                 uid, peer_id)
    peer = mngt.context.peer_store.get(peer_id)

    if mngt.context.object_store.get(uid) is not None:
        mngt.send_entity_found_interest(peer, uid)


def on_find_entity_timeout(interest):
    peer_id, uid = mngt.get_peer_uid_tuple(interest)

    if uid not in mngt.recorvering_registry:
        return

    recorvery_obj = mngt.recorvering_registry[uid]
    del mngt.recorvering_registry[uid]

    if not recorvery_obj['peers']:
        logger.debug('Fail to found entity %d', uid)
        mngt.fetch_callbacks.pop(uid, None)
        for failed_cb in recorvery_obj['failed']:
            failed_cb()
    else:
        logger.debug('Entity %d found at peers %s',
                     uid, recorvery_obj['peers'])

        try:
            # TODO: Arbitrary choice, to be replaced by latest version choice
            peer = next(filter(None, (mngt.context.peer_store.get(peer_id)
                                      for peer_id in recorvery_obj['peers'])))
            mngt.send_fetch_entity_interest(peer, uid)

        # Remote peers left during recorvery
        except StopIteration:
            logger.debug(
                'All found peers left before recorvery was finished, failing.')
            for failed_cb in recorvery_obj['failed']:
                failed_cb()


# EntityFoundInterest

def send_entity_found_interest(peer, uid):
    logger.debug('Sending EntityFoundInterest for entity %d to peer %d',
                 uid, peer.uid)
    name = pyndn.Name(peer.prefix) \
        .append('entity_found') \
        .append(str(uid)) \
        .append(str(mngt.context.peer_id))
    mngt.context.face.expressInterest(
        name,
        utils.on_dummy_data)


@mngt.register_interest_filter('local', utils.entity_found_regex)
def on_entity_found_interest(prefix, interest, face, interest_filter_id):
    peer_id, uid = mngt.get_peer_uid_tuple(interest)
    logger.debug('Entity %d found at peer %d', uid, peer_id)
    if uid in mngt.recorvering_registry:
        mngt.recorvering_registry[uid]['peers'].append(peer_id)
