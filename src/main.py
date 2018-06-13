import random
import logging
import sys

import app


def input_default(prompt, default):
    value = input('%s [%s] ' % (prompt, default))
    if not value:
        return default
    return value


def main():
    logging.getLogger().setLevel(logging.DEBUG)
    # NOTE: Temporary code before implementing real arguments parsing
    """
    pseudo = input_default('pseudo', 'toto')
    game_id = input_default('game_id', random.getrandbits(64))
    peer_id = input_default('peer_id', random.getrandbits(64))
    """
    _, game_id, peer_id = sys.argv
    logging.info('Starting app with game_id=%s and peer_id=%s', game_id, peer_id)

    my_app = app.App(int(game_id), 'toto', int(peer_id))
    my_app.run()


if __name__ == '__main__':
    main()
