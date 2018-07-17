import logging

import pyndn

from bakasable import utils
from bakasable.entities.mngt.actions import *
from bakasable.entities.mngt.common import *
from bakasable.entities.mngt.coordinator import *
from bakasable.entities.mngt.chunk import *
from bakasable.entities.mngt.chunk_notif import *
from bakasable.entities.mngt.entity import *
from bakasable.entities.mngt.recorvery import *
from bakasable.entities.mngt.update import *


logger = logging.getLogger(__name__)

recorvering_registry = {}
pending_fetch = set()
pending_update_interest = {}
watched_chunks = set()
player_watch = set()
fetch_callbacks = {}
context = None


def start(ctx):
    global context
    context = ctx

    context.face.registerPrefix(
        pyndn.Name(context.local_name),
        None,
        utils.on_registration_failed,
        utils.on_registration_success)

    context.face.registerPrefix(
        pyndn.Name(context.broadcast_name),
        None,
        utils.on_registration_failed,
        utils.on_registration_success)

    set_interest_filter()
