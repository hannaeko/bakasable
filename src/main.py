import random
import logging

import app


def input_default(prompt, default):
    value = input('%s [%s] ' % (prompt, default))
    if not value:
        return default
    return value


def main():
    logging.getLogger().setLevel(logging.DEBUG)

    pseudo = input_default('pseudo', 'toto')
    game_id = input_default('game_id', random.getrandbits(64))
    peer_id = input_default('peer_id', random.getrandbits(64))

    my_app = app.App(game_id, pseudo, peer_id)
    my_app.run()


if __name__ == '__main__':
    main()
