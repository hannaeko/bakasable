import logging
import os


logger = logging.getLogger(__name__)


broadcast_name_uri = '/ndn/broadcast/mygame'
default_local_name_uri = '/localhost/mygame'
prefix_discovery_uri = '/localhop/nfd/rib/routable-prefixes'

# match /chunk/<chunk x>/<chunk y>/entities
chunk_entites_regex = '<chunk><-?[0-9]+>{2}<entities>'

# match /chunk/<chunk x>/<chunk y>/enter/<entity uid>
enter_chunk_regex = '<chunk><-?[0-9]+>{2}<enter><[0-9]+>'

# match /coordinator/<entity uid>/<peer uid>
find_coordinator_regex = '<coordinator><[0-9]+>{2}'

# match /entity/<entity uid>/<peer uid>
find_entity_regex = '<entity><[0-9]+>{2}'

# match /entity_found/<entity uid>/<peer uid>
entity_found_regex = '<entity_found><[0-9]+>{2}'

# match /entity/<entity uid>/fetch
entity_fetch_regex = '<entity><[0-9]+><fetch>'

module_path = os.path.abspath(os.path.dirname(__file__))
asset_path = os.path.join(module_path, 'assets')


def on_registration_success(prefix, registered_prefix_id):
    logger.info(
        'Registered prefix %s under id %d' % (
            prefix.toUri(), registered_prefix_id))


def on_registration_failed(prefix):
    logger.error('Failed to register prefix %s' % prefix.toUri())


def on_timeout(interest):
    logger.warning('Timeout for interest %s' % interest.getName().toUri())


def on_dummy_data(interest, data):
    pass
