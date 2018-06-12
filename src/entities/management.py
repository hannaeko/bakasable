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

        events.local_prefix_discovered.connect(self.register_prefix)

    def register_prefix(self, local_name_uri):
        self.context.face.registerPrefix(
            pyndn.Name(local_name_uri),
            None,
            utils.on_registration_failed,
            utils.on_registration_success)

        self.context.face.setInterestFilter(
            pyndn.InterestFilter(local_name_uri, utils.chunk_entites_regex),
            self.on_chunk_entities_interest)

    def load_chunk(self, x, y, callback=None):
        """
        Load chunk at chunk coordinates x and y.

        If the local peer is reponsible of the chunk, create it.
        Else request it from a remote peer.

        If provided, call the callback with no argument when data is available
        in store.
        """
        chunk_uid = entities.objects.MapChunk.gen_uid(
            self.context.game_id, x, y)
        chunk_peer = peers.peer_store.get_closest_peer(chunk_uid)

        if chunk_peer.uid == self.peer_id:
            self.create_chunk(x, y)
            if callback is not None:
                callback()

        name = pyndn.Name(chunk_peer.prefix) \
            .append('chunk') \
            .append(str(x)).append(str(y)) \
            .append('entities')
        self.context.face.expressInterest(
            name,
            functools.partial(self.on_chunk_entities_data, callback),
            utils.on_timeout)

    def on_chunk_entities_interest(self, prefix, interest, face, interest_filter_id):
        x = int(interest.getName().get(-3))
        y = int(interest.getName().get(-2))

        chunk_uid = entities.objects.MapChunk.gen_uid(
            self.context.game_id, x, y)
        chunk = self.context.entity_store.get(chunk_uid)
        if chunk is not None:
            self.send_chunk_entites_data(interest, face, chunk)

    def send_chunk_entities_data(self, interest, face, map_chunk):
        chunk = entities.Chunk.deserialize(
            entities.Chunk(map=map_chunk, entities=()))

        chunk_data = pyndn.Data(interest.getName())
        chunk_data.setContent(chunk)
        face.putData(chunk_data)

    def on_chunk_entities_data(self, callback, interest, data):
        _, chunk = entities.Chunk.deserialize(data.getContent().toBytes())
        self.context.entity_store.add(chunk.map)
        self.context.entity_store.add(chunk.entities)
