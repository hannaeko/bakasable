import select
import time
import sys

import pyndn
import pyndn.security

import peers
import entities


class App(object):
    def __init__(self, game_id, pseudo, peer_id):
        self.game_id = game_id
        self.pseudo = pseudo
        self.peer_id = peer_id

        self.keychain = pyndn.security.KeyChain()

        self.face = pyndn.Face('192.168.20.161')
        self.face.setCommandSigningInfo(
            self.keychain, self.keychain.getDefaultCertificateName())
        self.peers_mngt = peers.PeerManagement(
            self.face, self.game_id, self.peer_id)
        self.entities_mngt = entities.EntityManagement(self)

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
