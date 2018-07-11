import os
import logging

import pygame

from bakasable.const import FRAME_LENGTH
from bakasable.utils import asset_path


logger = logging.getLogger(__name__)


class Sprite:
    cache = {}

    def __init__(self, filename, animated=False, loop=True):
        logger.info('Loading sprite "%s"', filename)
        if filename in self.cache:
            logger.debug('Sprite "%s", cache hit', filename)
            self.frames = self.cache[filename]
        else:
            logger.debug(
                'Sprite "%s", cache miss, loading from filesystem', filename)
            sprite_path = os.path.join(asset_path, filename)
            if os.path.isdir(sprite_path):
                frames_path = [entry.path for entry in os.scandir(sprite_path)]
                frames_path.sort()
            else:
                frames_path = [sprite_path]

            self.frames = []
            for frame_path in frames_path:
                self.frames.append(pygame.image.load(frame_path))
            self.cache[filename] = self.frames

        self.animation_length = FRAME_LENGTH * len(self.frames)
        self.current_frame = self.frames[0]
        self.total_time = self.start_time = 0
        self.loop = loop
        self.animated = animated

    def update(self, dt):
        self.total_time += dt

        animated = self.animated and (
            self.loop or
            self.total_time < self.start_time + self.animation_length)

        if animated:
            self.current_frame = self.frames[
                (self.total_time // FRAME_LENGTH) % len(self.frames)]

    def start_animation(self, loop=True):
        self.animated = True
        self.start_time = self.total_time
        self.loop = loop

    def stop_animation(self):
        self.animated = False
