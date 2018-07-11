import select
import time
import sys

import pyndn
import pyndn.security
import pygame

from bakasable import (
    utils,
    peers,
    entities,
    game,
    think
)
import bakasable.logic.loop  # register on_loop think functions
import bakasable.logic.game  # register on_event think functions


class App(object):
    def __init__(self, host, game_id, pseudo, peer_id, graphics=True):
        global context
        context = self

        self.game_id = game_id
        self.pseudo = pseudo
        self.peer_id = peer_id
        self.graphics = graphics

        self.keychain = pyndn.security.KeyChain()

        self.face = pyndn.Face(host)
        self.face.setCommandSigningInfo(
            self.keychain, self.keychain.getDefaultCertificateName())

        self.broadcast_name = pyndn.Name(utils.broadcast_name_uri) \
            .append(str(self.game_id))

        self.peers_mngt = peers.PeerManagement(self)
        # self.entities_mngt = entities.EntityManagement(self)

        self.peer_store = peers.PeerStore()
        self.object_store = entities.ObjectStore(self)

        self.clock = pygame.time.Clock()
        self.game = game.Game(self)

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
        self.local_name = pyndn.Name(new_prefix) \
            .append(str(self.game_id)) \
            .append(str(self.peer_id))

    #######
    # App #
    #######

    def run(self):
        self.start()
        entities.mngt.load_entity(self.peer_id)
        while self.carry_on:
            self.dt = self.clock.tick_busy_loop(20)
            self.loop()
            self.pending_input = select.select([sys.stdin, ], [], [], 0.0)[0]
            self.carry_on = self.carry_on and not self.pending_input
        self.stop()

    def start(self):
        self.carry_on = True
        self.connected = False

        self.peers_mngt.start()
        entities.mngt.start(self)

        while not self.connected:
            self.face.processEvents()
            time.sleep(0.01)

    def stop(self):
        if self.pending_input:
            input()
        self.peers_mngt.stop()
        self.face.shutdown()

    def loop(self):
        self.face.processEvents()
        think.on_loop.exec_all(self)
        self.game.process_events()
        self.game.loop()
