import logging
import pyndn

import utils
import entities


class PeerManagement(object):
    def __init__(self, context):
        self.context = context

        self.local_name = pyndn.Name()

        self.broadcast_name = pyndn.Name(utils.broadcast_name_uri) \
            .append(str(self.context.game_id))

        self.context.face.registerPrefix(
            pyndn.Name(self.broadcast_name).append('join'),
            self.on_join_interest,
            utils.on_registration_failed,
            utils.on_registration_success)

        self.context.face.registerPrefix(
            pyndn.Name(self.broadcast_name).append('leave'),
            self.on_leave_interest,
            utils.on_registration_failed,
            utils.on_registration_success)

    def start(self):
        self.local_name = pyndn.Name(self.context.app_name) \
            .append(str(self.context.game_id)) \
            .append(str(self.context.peer_id))

        self.context.peer_store.add(
            entities.Peer(
                uid=self.context.peer_id,
                prefix=self.local_name.toUri()))

        self.send_join_interest()

    def stop(self):
        self.send_leave_interest()

    ################
    # Join process #
    ################

    def send_join_interest(self):
        join_name = pyndn.Name(self.broadcast_name) \
            .append('join') \
            .append(self.local_name)

        self.context.face.expressInterest(
            join_name,
            self.on_peer_info_list_data,
            utils.on_timeout)

    def on_join_interest(self, prefix, interest, face, interest_filter_id):
        backroute = interest.getName().getSubName(5)
        peer_id = int(backroute.get(-1).toEscapedString())

        new_peer = entities.Peer(uid=peer_id, prefix=backroute.toUri())
        logging.debug('Join interest received from %s' % peer_id)

        clst_uid = self.context.peer_store.get_closest_uid(peer_id)
        if clst_uid == self.context.peer_id:
            logging.info('Sending peer list to %d' % peer_id)
            self.send_peer_info_list_data(interest, face)

        self.context.peer_store.add(new_peer)
        logging.info('Peer %s added to store' % new_peer)

    def send_peer_info_list_data(self, interest, face):
        peer_list_info_data = pyndn.Data(interest.getName())
        peer_list_info_data.setContent(
            entities.PeerArray.serialize(self.context.peer_store.values()))

        face.putData(peer_list_info_data)

    def on_peer_info_list_data(self, interest, data):
        logging.debug('Got peer list')
        _, peer_array = entities.PeerArray.deserialize(
            data.getContent().toBytes())

        self.context.peer_store.add(*peer_array)

    #################
    # Leave process #
    #################

    def send_leave_interest(self):
        leave_name = pyndn.Name(self.broadcast_name) \
            .append('leave') \
            .append(str(self.context.peer_id))

        self.context.face.expressInterest(
            leave_name,
            utils.on_dummy_data)

    def on_leave_interest(self, prefix, interest, face, interest_filter_id):
        peer_id = int(interest.getName().get(-1).toEscapedString())
        leaving_peer = self.context.peer_store.pop(peer_id, None)

        logging.debug('Leave interest received from %d' % peer_id)

        if leaving_peer is not None:
            logging.info('Peer %s removed from store' % leaving_peer)
