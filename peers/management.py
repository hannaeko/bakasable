import logging
import pyndn

import utils
import events
import peers
import entities


class PeerManagement(object):
    def __init__(self, face, game_id, peer_id):
        self.face = face
        self.game_id = game_id
        self.peer_id = peer_id

        self.local_name = pyndn.Name()

        self.broadcast_name = pyndn.Name(utils.broadcast_name_uri) \
            .append(str(self.game_id))

        self.face.registerPrefix(
            pyndn.Name(self.broadcast_name).append('join'),
            self.on_join_interest,
            utils.on_registration_failed,
            utils.on_registration_success)

        self.face.registerPrefix(
            pyndn.Name(self.broadcast_name).append('leave'),
            self.on_leave_interest,
            utils.on_registration_failed,
            utils.on_registration_success)

        events.local_prefix_discovered.connect(self.on_local_prefix_discovered)

    def start(self):
        self.send_prefix_discovery_interest()

    def stop(self):
        self.send_leave_interest()

    ####################
    # Prefix discovery #
    ####################

    def send_prefix_discovery_interest(self):
        name = pyndn.Name(utils.prefix_discovery_uri)
        self.face.expressInterest(
            name,
            self.on_prefix_discovery_data,
            self.on_prefix_discovery_timeout)

    def on_prefix_discovery_data(self, interest, data):
        new_prefix = pyndn.Name()
        new_prefix.wireDecode(data.getContent())
        events.local_prefix_discovered.send(new_prefix.toUri())

    def on_prefix_discovery_timeout(self, interest):
        events.local_prefix_discovered.send(utils.default_local_name_uri)

    def on_local_prefix_discovered(self, new_prefix):
        self.local_name = pyndn.Name(new_prefix) \
            .append(str(self.game_id)) \
            .append(str(self.peer_id))

        peers.peer_store.add(
            entities.Peer(uid=self.peer_id, prefix=self.local_name.toUri()))

        self.send_join_interest()

    ################
    # Join process #
    ################

    def send_join_interest(self):
        join_name = pyndn.Name(self.broadcast_name) \
            .append('join') \
            .append(self.local_name)

        self.face.expressInterest(
            join_name,
            self.on_peer_info_list_data,
            utils.on_timeout)

    def on_join_interest(self, prefix, interest, face, interest_filter_id):
        backroute = interest.getName().getSubName(5)
        peer_id = int(backroute.get(-1).toEscapedString())

        new_peer = entities.Peer(uid=peer_id, prefix=backroute.toUri())
        logging.debug('Join interest received from %s' % peer_id)

        clst_uid = peers.peer_store.get_closest_uid(peer_id)
        if clst_uid == self.peer_id:
            logging.info('Sending peer list to %d' % peer_id)
            self.send_peer_info_list_data(interest, face)

        peers.peer_store.add(new_peer)
        logging.info('Peer %s added to store' % new_peer)

    def send_peer_info_list_data(self, interest, face):
        peer_list_info_data = pyndn.Data(interest.getName())
        peer_list_info_data.setContent(
            entities.PeerArray.serialize(peers.peer_store.values()))

        face.putData(peer_list_info_data)

    def on_peer_info_list_data(self, interest, data):
        logging.debug('Got peer list')
        _, peer_array = entities.PeerArray.deserialize(
            data.getContent().toBytes())

        peers.peer_store.add(*peer_array)

    #################
    # Leave process #
    #################

    def send_leave_interest(self):
        leave_name = pyndn.Name(self.broadcast_name) \
            .append('leave') \
            .append(str(self.peer_id))

        self.face.expressInterest(
            leave_name,
            utils.on_dummy_data)

    def on_leave_interest(self, prefix, interest, face, interest_filter_id):
        peer_id = int(interest.getName().get(-1).toEscapedString())
        leaving_peer = peers.peer_store.pop(peer_id, None)

        logging.debug('Leave interest received from %d' % peer_id)

        if leaving_peer is not None:
            logging.info('Peer %s removed from store' % leaving_peer)
