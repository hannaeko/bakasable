import logging


broadcast_name_uri = '/ndn/broadcast/mygame'
default_local_name_uri = '/localhost/mygame'
prefix_discovery_uri = '/localhop/nfd/rib/routable-prefixes'

# match /chunk/<chunk x>/<chunk y>/entities
chunk_entites_regex = '<chunk><-?[0-9]+>{2}<entities>'


def on_registration_success(prefix, registered_prefix_id):
    logging.info(
        'Registered prefix %s under id %d' % (
            prefix.toUri(), registered_prefix_id))


def on_registration_failed(prefix):
    logging.error('Failed to register prefix %s' % prefix.toUri())


def on_timeout(interest):
    logging.warning('Timeout for interest %s' % interest.getName().toUri())


def on_dummy_data(interest, data):
    pass
