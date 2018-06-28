import logging
import functools

import pyndn

from bakasable import (
    utils,
    entities,
    const
)
from bakasable.entities import mngt


logger = logging.getLogger(__name__)


def load_entity(uid, callback=None):
    mngt.add_fetch_callback(uid, callback)

    # Already in store and active
    if uid in mngt.context.object_store.store and \
       mngt.context.object_store.store.get(uid).active:

        mngt.context.object_store.set_local_coordinator(uid)
        mngt.execute_callback(uid)
        return

    if uid in mngt.pending_fetch:  # Already loading entity
        return

    mngt.pending_fetch.add(uid)

    if uid == mngt.context.peer_id:  # fetching local player
        logger.info('Loading local player')
        mngt.start_recorvery(uid, failed_cb=mngt.create_player)
    elif mngt.context.peer_store.get_closest_uid(uid) == mngt.context.peer_id:
        mngt.start_recorvery(uid)
    else:
        peer = mngt.context.peer_store.get_closest_peer(uid)
        logger.info('Loading entity %d from peer %d', uid, peer.uid)
        mngt.send_fetch_entity_interest(peer, uid)


def send_fetch_entity_interest(peer, uid):
    logger.debug('Sending FetchEntityInterest for entity %d to peer %d',
                 uid, peer.uid)
    name = pyndn.Name(peer.prefix) \
        .append('entity') \
        .append(str(uid)) \
        .append('fetch')
    interest = pyndn.Interest(name)
    # About three times a normal timeout as two timeout may occur before
    # the chunk is created.
    interest.setInterestLifetimeMilliseconds(30000)
    mngt.context.face.expressInterest(
        interest,
        mngt.on_fetch_entity_data,
        mngt.on_fetch_entity_timeout)


@mngt.register_interest_filter('local', utils.entity_fetch_regex)
def on_fetch_entity_interest(prefix, interest, face, interest_filter_id):
    uid = int(interest.getName().get(-2).toEscapedString())
    logger.debug('Received FetchEntityInterest for entity %d', uid)

    entity = mngt.context.object_store.get(uid)
    if entity is not None:
        return mngt.send_fetch_entity_data(interest, face, entity)
    mngt.start_recorvery(
        uid,
        success_cb=functools.partial(
            mngt.send_fetch_entity_data, interest, face, uid),
        failed_cb=funmngt.send_deleted_entity_data)


def send_fetch_entity_data(interest, face, entity_or_uid):
    if isinstance(entity_or_uid, int):
        entity = mngt.context.object_store.get(entity_or_uid)
    else:
        entity = entity_or_uid

    logger.debug('Sending FetchEntityData for entity %d', entity.uid)

    result = entities.Result(
        status=const.status_code.OK, value=entity)

    fetch_entity_data = pyndn.Data(interest.getName())
    fetch_entity_data.setContent(entities.Result.serialize(result))
    face.putData(fetch_entity_data)


def send_deleted_entity_data(interest, face):
    logger.debug('Sending DeletedEntityData for interest %s',
                 interest.getName().toUri())

    result = entities.Result(
        status=const.status_code.DELETED_ENTITY, value=None)
    deleted_entity_data = pyndn.Data(interest.getName())
    deleted_entity_data.setContent(entities.Result.serialize(result))

    face.putData(deleted_entity_data)


def on_fetch_entity_data(interest, data):
    uid = int(interest.getName().get(-2).toEscapedString())
    mngt.pending_fetch.remove(uid)
    _, result = entities.Result.deserialize(data.getContent().toBytes())

    logger.debug('Received FetchEntityData for entity %d (status=%d)',
                 uid, result.status)

    if result.status == const.status_code.DELETED_ENTITY:
        mngt.context.object_store.remove(uid)
        mngt.fetch_callbacks.pop(uid, None)
    elif result.status == const.status_code.OK:
        mngt.context.object_store.add(result.value)
        mngt.execute_callback(uid)


def on_fetch_entity_timeout(interest):
    uid = int(interest.getName().get(-2).toEscapedString())
    mngt.pending_fetch.remove(uid)
    mngt.fetch_callbacks.pop(uid, None)
    utils.on_timeout(interest)


def create_player():
    if mngt.context.peer_id in mngt.pending_fetch:
        mngt.pending_fetch.remove(mngt.context.peer_id)

    player = entities.Player(
        uid=mngt.context.peer_id, x=0, y=0, pseudo=mngt.context.pseudo)
    mngt.context.object_store.add(player)
    logger.debug('Created player %s' % player)
    mngt.send_enter_chunk_interest(player)
    return player
