import random
import logging
import sys
import argparse

import bakasable
import bakasable.debug


logger = logging.getLogger(__name__)


def setup_logger():
    root_logger = logging.getLogger()
    ch = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s#%(lineno)d - %(message)s')
    ch.setFormatter(formatter)
    root_logger.addHandler(ch)

    logging.TRACE = 9
    logging.addLevelName(logging.TRACE, 'TRACE')

    def trace(self, message, *args, **kwargs):
        if self.isEnabledFor(logging.TRACE):
            self._log(logging.TRACE, message, args, **kwargs)

    logging.Logger.trace = trace
    root_logger.setLevel(logging.DEBUG)


def main():
    setup_logger()

    parser = argparse.ArgumentParser(
        prog='bakasable',
        description=' Peer to peer multiplayer sandbox game based on NDN.')

    parser.add_argument(
        '--game', '-g',
        metavar='<game_id>',
        help='Set the game id to connect to.',
        default=random.getrandbits(64),
        type=int)

    parser.add_argument(
        '--peer', '-p',
        metavar='<peer_id>',
        help='Set the peer id.',
        default=random.getrandbits(64),
        type=int)

    parser.add_argument(
        '--pseudo', '-P',
        metavar='<pseudo>',
        help='Set player pseudo.',
        default='toto')

    parser.add_argument(
        '--disable-graphics', '-d',
        help='Disable graphical interface',
        action='store_true'
    )

    parser.add_argument(
        '--debug', '-D',
        help='Display debug tool',
        action='store_true')

    args = parser.parse_args()

    logger.info('Starting app with game_id=%s and peer_id=%s',
                args.game, args.peer)
    my_app = bakasable.App(args.game,
                           args.pseudo,
                           args.peer,
                           not args.disable_graphics)
    if args.debug:
        logger.info('Starting debug tool')
        debug_tool = bakasable.debug.DebugTool(my_app)

    my_app.run()

    if args.debug:
        debug_tool.root.quit()


if __name__ == '__main__':
    main()
