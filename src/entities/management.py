import math
import hashlib
import struct
import logging
import functools

import pyndn

import const.status_code
import utils
import peers
import entities
import logic.chunk


logger = logging.getLogger(__name__)


class EntityManagement(object):
    def __init__(self, context):
        self.context = context
        self.recorvering_registry = {}

    def start(self):
        self.context.face.registerPrefix(
            pyndn.Name(self.context.local_name),
            None,
            utils.on_registration_failed,
            utils.on_registration_success)

        self.context.face.registerPrefix(
            pyndn.Name(self.context.broadcast_name),
            None,
            utils.on_registration_failed,
            utils.on_registration_success)

        # ChunkEntitiesInterest
        self.context.face.setInterestFilter(
            pyndn.InterestFilter(
                self.context.local_name, utils.chunk_entites_regex),
            self.on_chunk_entities_interest)

        # FindCoordinatorInterest
        self.context.face.setInterestFilter(
            pyndn.InterestFilter(
                self.context.broadcast_name, utils.find_coordinator_regex),
            self.on_find_coordinator_interest)

        # FindEntityInterest
        self.context.face.setInterestFilter(
            pyndn.InterestFilter(
                self.context.broadcast_name, utils.find_entity_regex),
            self.on_find_entity_interest)

        # EntityFoundInterest
        self.context.face.setInterestFilter(
            pyndn.InterestFilter(
                self.context.local_name, utils.entity_found_regex),
            self.on_entity_found_interest)

        # FetchEntityInterest
        self.context.face.setInterestFilter(
            pyndn.InterestFilter(
                self.context.local_name, utils.entity_fetch_regex),
            self.on_fetch_entity_interest)

    def get_peer_uid_tuple(self, interest):
        peer_id = int(interest.getName().get(-1).toEscapedString())
        uid = int(interest.getName().get(-2).toEscapedString())
        return peer_id, uid

    #########
    # Chunk #
    #########

    def load_chunk(self, x, y):
        """
        Load chunk at chunk coordinates x and y.

        If the local peer is coordinator of the chunk, try to get the chunk
        from remotes before creating it. Else request it from a remote peer.
        """
        chunk_uid = entities.MapChunk.gen_uid(
            self.context.game_id, x, y)
        chunk_peer = self.context.peer_store.get_closest_peer(chunk_uid)

        logger.info('Loading chunk %d (%d, %d) from peer %d', chunk_uid, x, y, chunk_peer.uid)
        if chunk_peer.uid == self.context.peer_id:
            self.start_recorvery(
                chunk_uid,
                failed_cb=functools.partial(self.create_chunk, x, y))
        else:
            self.send_chunk_entities_interest(chunk_peer, x, y)

    def send_chunk_entities_interest(self, chunk_peer, x, y):
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
        self.context.face.expressInterest(
            interest,
            self.on_chunk_entities_data,
            utils.on_timeout)

    def on_chunk_entities_interest(self, prefix, interest, face, interest_filter_id):
        """
        Try to get the requested chunk from the local store and send it back if
        found.
        Else initiate the recorvery procedure with the chunk id before creating
        the chunk if it did not managed to find it in remote peers store.
        """
        x = int(interest.getName().get(-3).toEscapedString())
        y = int(interest.getName().get(-2).toEscapedString())

        chunk_uid = entities.MapChunk.gen_uid(
            self.context.game_id, x, y)
        chunk = self.context.object_store.get(chunk_uid)

        logger.debug('Received ChunkEntitiesInterest for chunk %d (%d, %d)', chunk_uid, x, y)
        if chunk is not None:
            return self.send_chunk_entities_data(
                interest, face, entities.Chunk(map=chunk, entities=()))

        cb = functools.partial(self.send_chunk_or_create, interest, face, x, y)
        self.start_recorvery(
            chunk_uid,
            failed_cb=cb,  # Failure : create then send
            success_cb=cb)  # Success : fetch in store then send

    def send_chunk_entities_data(self, interest, face, chunk):
        logger.debug('Sending ChunkEntitiesData for chunk %d (%d, %d)', chunk.map.uid, chunk.map.x, chunk.map.y)
        chunk = entities.Chunk.serialize(chunk)

        chunk_data = pyndn.Data(interest.getName())
        chunk_data.setContent(chunk)
        face.putData(chunk_data)

    def on_chunk_entities_data(self, interest, data):
        _, chunk = entities.Chunk.deserialize(data.getContent().toBytes())
        logger.debug('Received ChunkEntitiesData for chunk %d (%d, %d)', chunk.map.uid, chunk.map.x, chunk.map.y)
        self.context.object_store.add(chunk)

    def send_chunk_or_create(self, interest, face, x, y):
        chunk = self.create_chunk(x, y)
        self.send_chunk_entities_data(interest, face, chunk)

    def create_chunk(self, x, y):
        chunk_uid = entities.MapChunk.gen_uid(
            self.context.game_id, x, y)
        chunk = self.context.object_store.get(chunk_uid)

        # Chunk already exist in store, simply return it directly
        if chunk is not None:
            return entities.Chunk(map=chunk, entities=())

        chunk = logic.chunk.generate_chunk(self.context.game_id, x, y)
        self.context.object_store.add(chunk)
        logger.debug('Created chunk %s', chunk)
        # TODO: assign entities to peers.
        return chunk

    #############
    # Recorvery #
    #############

    def start_recorvery(self, uid, success_cb=None, failed_cb=None):
        logger.debug('Starting recorvery for entity %d', uid)
        if uid not in self.recorvering_registry:
            self.recorvering_registry[uid] = {
                'success': [],
                'failed': [],
                'peers': []
            }

        if success_cb:
            self.recorvering_registry[uid]['success'].append(success_cb)
        if failed_cb:
            self.recorvering_registry[uid]['failed'].append(failed_cb)

        self.send_find_coordinator_interest(uid)

    # FindCoordinatorInterest

    def send_find_coordinator_interest(self, uid):
        name = pyndn.Name(self.context.broadcast_name) \
            .append('coordinator') \
            .append(str(uid)) \
            .append(str(self.context.peer_id))
        logger.debug('Sending FindCoordinatorInterest to %s', name.toUri())
        self.context.face.expressInterest(
            name,
            self.on_find_coordinator_data,
            self.on_find_coordinator_timeout)

    def on_find_coordinator_interest(self, prefix, interest, face, interest_filter_id):
        peer_id, uid = self.get_peer_uid_tuple(interest)
        logger.debug('Received FindCoordinatorInterest for entity %d from peer %d', uid, peer_id)

        if not self.context.object_store.is_local_coordinator(uid):
            return
        entity = self.context.object_store.get(uid)

        # TODO: End pending update interests with CoordinatorChangedData

        self.context.object_store.set_local_coordinator(uid, False)
        self.send_find_coordinator_data(interest, face, entity)

    def send_find_coordinator_data(self, interest, face, entity):
        logger.debug('Sending FindCoordinatorData for entity %d', entity.uid)
        if isinstance(entity, entities.MapChunk):
            entity = entities.Chunk(map=entity, entities=[])

        final_object = entity.serialize(entity)

        find_coordinator_data = pyndn.Data(interest.getName())
        find_coordinator_data.setContent(final_object)
        face.putData(find_coordinator_data)

    def on_find_coordinator_data(self, interest, data):
        entity = entities.GameObject.deserialize(data.getContent().toBytes())
        self.context.object_store.add(entity)

        peer_id, uid = self.get_peer_uid_tuple(interest)
        logger.debug('Successfuly found coordinator for entity %d', uid)

        recorvery_obj = self.recorvering_registry[uid]
        del self.recorvering_registry[uid]

        for success_cb in recorvery_obj['success']:
            success_cb()

    def on_find_coordinator_timeout(self, interest):
        peer_id, uid = self.get_peer_uid_tuple(interest)

        logger.debug('Failed to find coordinator for entity %d', uid)
        self.send_find_entity_interest(uid)

    # FindEntityInterest

    def send_find_entity_interest(self, uid):
        logger.debug('Sending FindEntityInterest for entity %d', uid)
        name = pyndn.Name(self.context.broadcast_name) \
            .append('entity') \
            .append(str(uid)) \
            .append(str(self.context.peer_id))
        self.context.face.expressInterest(
            name,
            utils.on_dummy_data,
            self.on_find_entity_timeout)

    def on_find_entity_interest(self, prefix, interest, face, interest_filter_id):
        peer_id, uid = self.get_peer_uid_tuple(interest)
        logger.debug('Received FindEntityInterest for entity %d from peer %d', uid, peer_id)
        peer = self.context.peer_store.get(peer_id)

        if self.context.object_store.get(uid) is not None:
            self.send_entity_found_interest(peer, uid)

    def on_find_entity_timeout(self, interest):
        peer_id, uid = self.get_peer_uid_tuple(interest)

        if uid not in self.recorvering_registry:
            return

        recorvery_obj = self.recorvering_registry[uid]
        del self.recorvering_registry[uid]

        if not recorvery_obj['peers']:
            logger.debug('Fail to found entity %d', uid)
            for failed_cb in recorvery_obj['failed']:
                failed_cb()
        else:
            logger.debug('Entity %d found at peers %s', uid, recorvery_obj['peers'])

            # TODO: Arbitrary choice, to be replaced by latest version choice
            peer = self.context.peer_store.get(recorvery_obj['peers'][0])
            self.send_fetch_entity_interest(peer, uid)

    # EntityFoundInterest

    def send_entity_found_interest(self, peer, uid):
        logger.debug('Sending EntityFoundInterest for entity %d to peer %d', uid, peer.uid)
        name = pyndn.Name(peer.prefix) \
            .append('entity_found') \
            .append(str(uid)) \
            .append(str(self.context.peer_id))
        self.context.face.expressInterest(
            name,
            utils.on_dummy_data)

    def on_entity_found_interest(self, prefix, interest, face, interest_filter_id):
        peer_id, uid = self.get_peer_uid_tuple(interest)
        logger.debug('Entity %d found at peer %d', uid, peer_id)
        if uid in self.recorvering_registry:
            self.recorvering_registry[uid]['peers'].append(peer_id)

    ####################
    # Entity retrieval #
    ####################

    def load_entity(self, uid):
        peer = self.conext.peer_store.get_closest_peer(uid)
        logger.info('Loading entity %d from peer %d', uid, peer.uid)
        self.send_fetch_entity_interest(peer, uid)

    def send_fetch_entity_interest(self, peer, uid):
        logger.debug('Sending FetchEntityInterest for entity %d to peer %d', uid, peer.uid)
        name = pyndn.Name(peer.prefix) \
            .append('entity') \
            .append(str(uid)) \
            .append('fetch')
        interest = pyndn.Interest(name)
        # About three times a normal timeout as two timeout may occur before
        # the chunk is created.
        interest.setInterestLifetimeMilliseconds(30000)
        self.context.face.expressInterest(
            interest,
            self.on_fetch_entity_data,
            utils.on_timeout)

    def on_fetch_entity_interest(self, prefix, interest, face, interest_filter_id):
        uid = int(interest.getName().get(-2).toEscapedString())
        logger.debug('Received FetchEntityInterest for entity %d', uid)

        entity = self.context.object_store.get(uid)
        if entity is not None:
            return self.send_fetch_entity_data(interest, face, entity)
        self.start_recorvery(
            uid,
            success_cb=functools.partial(self.send_fetch_entity_data, interest, face, uid),
            failed_cb=funself.send_deleted_entity_data)

    def send_fetch_entity_data(self, interest, face, entity_or_uid):
        if isinstance(entity_or_uid, int):
            entity = self.context.object_store.get(entity_or_uid)
        else:
            entity = entity_or_uid

        logger.debug('Sending FetchEntityData for entity %d', entity.uid)

        result = entities.Result(status=const.status_code.OK, value=entity)

        fetch_entity_data = pyndn.Data(interest.getName())
        fetch_entity_data.setContent(entities.Result.serialize(result))
        face.putData(fetch_entity_data)

    def send_deleted_entity_data(self, interest, face):
        logger.debug('Sending DeletedEntityData for interest %s', interest.getName().toUri())

        result = entities.Result(
            status=const.status_code.DELETED_ENTITY, value=None)
        deleted_entity_data = pyndn.Data(interest.getName())
        deleted_entity_data.setContent(entities.Result.serialize(result))

        face.putData(deleted_entity_data)

    def on_fetch_entity_data(self, interest, data):
        uid = int(interest.getName().get(-2).toEscapedString())
        _, result = entities.Result.deserialize(data.getContent().toBytes())

        logger.debug('Received FetchEntityData for entity %d (status=%d)', uid, result.status)

        if result.status == const.status_code.DELETED_ENTITY:
            self.context.object_store.remove(uid)
        elif result.status == const.status_code.OK:
            self.context.object_store.add(result.value)
