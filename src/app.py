import select
import time
import sys

import pyndn
import pyndn.security

import peers
import entities
import utils


class App(object):
    def __init__(self, game_id, pseudo, peer_id):
        self.game_id = game_id
        self.pseudo = pseudo
        self.peer_id = peer_id

        self.keychain = pyndn.security.KeyChain()

        self.face = pyndn.Face('192.168.20.167')
        self.face.setCommandSigningInfo(
            self.keychain, self.keychain.getDefaultCertificateName())

        self.peers_mngt = peers.PeerManagement(self)
        # self.entities_mngt = entities.EntityManagement(self)
        self.peer_store = peers.PeerStore()

        self.prefix_discovered = False
        self.send_prefix_discovery_interest()
        while not self.prefix_discovered:
            self.face.processEvents()
            time.sleep(0.01)

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
        self.on_local_prefix_discovered(new_prefix)

    def on_prefix_discovery_timeout(self, interest):
        self.on_local_prefix_discovered(utils.default_local_name_uri)

    def on_local_prefix_discovered(self, new_prefix):
        self.prefix_discovered = True
        self.app_name = pyndn.Name(new_prefix)

    #######
    # App #
    #######

    def run(self):
        self.start()
        while self.carry_on:
            self.loop()
            self.carry_on = not select.select([sys.stdin, ], [], [], 0.0)[0]
            time.sleep(0.01)
        self.stop()

    def start(self):
        self.carry_on = True
        self.peers_mngt.start()

    def stop(self):
        input()
        self.peers_mngt.stop()
        self.face.shutdown()

    def loop(self):
        self.face.processEvents()
