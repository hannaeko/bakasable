import math
import hashlib
import struct
import logging

import pyndn

import utils
import events
import peers
import entities
import logic.chunk


class EntityManagement(object):
    def __init__(self, face, game_id, peer_id):
        self.face = face
        self.game_id = game_id
        self.peer_id = peer_id

        events.local_prefix_discovered.connect(self.register_prefix)

    def register_prefix(self, local_name_uri):
        self.load_from(0, 0, 1)
        self.face.registerPrefix(
            pyndn.Name(local_name_uri),
            None,
            utils.on_registration_failed,
            utils.on_registration_success)

        self.face.setInterestFilter(
            pyndn.InterestFilter(local_name_uri, utils.chunk_entites_regex),
            self.on_chunk_entities_interest)

    #################
    # Chunk loading #
    #################

    def load_from(self, player_x, player_y, radius):
        player_chunck_x = math.floor((player_x / 15))
        player_chunck_y = math.floor((player_y / 15))

        for x in range(player_chunck_x - radius, player_chunck_x + radius + 1):
            for y in range(player_chunck_y - radius, player_chunck_y + radius + 1):
                self.load_chunk(x, y)

    def load_chunk(self, x, y):
        chunk_uid = entities.MapChunk.gen_uid(self.game_id, x, y)
        chunk_peer = peers.peer_store.get_closest_peer(chunk_uid)

        logging.debug(
            'Loading chunk %d,%d from peer %d' % (x, y, chunk_peer.uid))
        if self.peer_id == chunk_peer.uid:
            self.create_chunk(self, x, y)
        else:
            self.send_chunk_entities_interest(chunk_peer.prefix, x, y)

    def send_chunk_entities_interest(self, peer_prefix, chunk_x, chunk_y):
        chunk_entities_name = pyndn.Name(peer_prefix) \
            .append(str(chunk_x)) \
            .append(str(chunk_y)) \
            .append('entities')

        self.face.expressInterest(
            chunk_entities_name,
            self.on_chunk_entities_data,
            utils.on_timeout)

    def on_chunk_entities_interest(self, prefix, interest, face, interest_filter_id):
        chunk_uid = entities.MapChunk.gen_uid(self.game_id, x, y)
        chunk = entities.object_store.get_chunk(x, y)

    def on_chunk_entities_data(self, interest, data):
        logging.debug('Received chunk data.')

    ####################
    # Chunk generation #
    ####################

    def create_chunk(self, x, y):
        chunk = logic.chunk.generate_chunk(self.game_id, x, y)
        entities.object_store.add(chunk)
        return chunk
