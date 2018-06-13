import math
import hashlib
import struct
import logging
import functools

import pyndn

import utils
import events
import peers
import entities
import logic.chunk


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

        # EntityFoundInterest
        self.context.face.setInterestFilter(
            pyndn.InterestFilter(
                self.context.local_name, utils.entity_found_regex),
            self.on_entity_found_interest)

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

        logging.info('Loading chunk %d (%d, %d) from peer %d', chunk_uid, x, y, chunk_peer.uid)
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
        logging.debug('Sending ChunkEntitiesInterest to %s', name.toUri())
        self.context.face.expressInterest(
            name,
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

        logging.debug('Received ChunkEntitiesInterest for chunk %d (%d, %d)', chunk_uid, x, y)
        if chunk is not None:
            import pdb; pdb.set_trace()
            return self.send_chunk_entities_data(
                interest, face, entities.Chunk(map=chunk, entities=()))

        cb = functools.partial(self.send_chunk_or_create, interest, face, x, y)
        self.start_recorvery(
            chunk_uid,
            failed_cb=cb,  # Failure : create then send
            success_cb=cb)  # Success : fetch in store then send

    def send_chunk_entities_data(self, interest, face, chunk):
        logging.debug('Sending ChunkEntitiesData for chunk %d (%d, %d)', chunk.map.uid, chunk.map.x, chunk.map.y)
        chunk = entities.Chunk.serialize(chunk)

        chunk_data = pyndn.Data(interest.getName())
        chunk_data.setContent(chunk)
        face.putData(chunk_data)

    def on_chunk_entities_data(self, interest, data):
        _, chunk = entities.Chunk.deserialize(data.getContent().toBytes())
        logging.debug('Received ChunkEntitiesData for chunk %d (%d, %d)', chunk.map.uid, chunk.map.x, chunk.map.y)
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
        self.context.object_store.add(chunk, coordinator=True)
        logging.debug('Created chunk %s', chunk)
        # TODO: assign entities to peers.
        return chunk

    #############
    # Recorvery #
    #############

    def start_recorvery(self, uid, success_cb=None, failed_cb=None):
        logging.debug('Starting recorvery for entity %d', uid)
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
        logging.debug('Sending FindCoordinatorInterest to %s', name.toUri())
        self.context.face.expressInterest(
            name,
            self.on_find_coordinator_data,
            self.on_find_coordinator_timeout)

    def on_find_coordinator_interest(self, prefix, interest, face, interest_filter_id):
        peer_id, uid = self.get_peer_uid_tuple(interest)
        logging.debug('Received FindCoordinatorInterest for entity %d from peer %d', uid, peer_id)

        if not self.context.object_store.is_local_coordinator(uid):
            return
        entity = self.context.object_store.get(uid)
        self.context.object_store.set_local_coordinator(uid, False)
        self.send_find_coordinator_data(interest, face, entity)

    def send_find_coordinator_data(self, interest, face, entity):
        logging.debug('Sending FindCoordinatorData for entity %d', entity.uid)
        if isinstance(entity, entities.MapChunk):
            # TODO: Find all entity on chunk
            entity = entities.Chunk(map=entity, entities=[])

        final_object = entity.serialize(entity)

        find_coordinator_data = pyndn.Data(interest.getName())
        find_coordinator_data.setContent(final_object)
        face.putData(find_coordinator_data)

    def on_find_coordinator_data(self, interest, data):
        entity = entities.GameObject.deserialize(data.getContent().toBytes())
        self.context.object_store.add(entity)

        peer_id, uid = self.get_peer_uid_tuple(interest)
        logging.debug('Successfuly found coordinator for entity %d', uid)

        recorvery_obj = self.recorvering_registry[uid]
        del self.recorvering_registry[uid]

        for success_cb in recorvery_obj['success']:
            success_cb()

    def on_find_coordinator_timeout(self, interest):
        peer_id, uid = self.get_peer_uid_tuple(interest)

        logging.debug('Failed to find coordinator for entity %d', uid)
        self.send_find_entity_interest(uid)

    # FindEntityInterest

    def send_find_entity_interest(self, uid):
        logging.debug('Sending FindEntityInterest for entity %d', uid)
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
        logging.debug('Received FindEntityInterest for entity %d from peer %d', uid, peer_id)
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
            logging.debug('Fail to found entity %d', uid)
            for failed_cb in recorvery_obj['failed']:
                failed_cb()
        else:
            logging.debug('Entity %d found at peers %s', uid, recorvery_obj['peers'])
            # TODO: Fetch entity

    # EntityFoundInterest

    def send_entity_found_interest(self, peer, uid):
        logging.debug('Sending EntityFoundInterest for entity %d to peer %d', uid, peer.uid)
        name = pyndn.Name(peer.prefix) \
            .append('entity_found') \
            .append(str(uid)) \
            .append(str(self.context.peer_id))
        self.context.face.expressInterest(
            name,
            utils.on_dummy_data)

    def on_entity_found_interest(self, prefix, interest, face, interest_filter_id):
        peer_id, uid = self.get_peer_uid_tuple(interest)
        logging.debug('Entity %d found at peer %d', uid, peer_id)
        if uid in self.recorvering_registry:
            self.recorvering_registry[uid]['peers'].append(peer_id)
