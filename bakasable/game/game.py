import logging

import pygame

from bakasable.logic.chunk import get_chunk_range
from bakasable.const import TILE_SIZE
from bakasable.think import on_event


logger = logging.getLogger(__name__)


class Game:
    def __init__(self, context):
        self.context = context
        if self.context.graphics:
            self.screen = pygame.display.set_mode((800, 600))
            pygame.display.set_caption('Bakasable - %d' % self.context.peer_id)
        else:
            self.screen = pygame.Surface((800, 600))

    def loop(self):
        if self.context.graphics:
            pygame.display.flip()

        player = self.context.object_store.get(self.context.peer_id)
        if not player:
            return

        screen_rect = self.screen.get_rect()
        self.screen.fill((0, 0, 0))

        top_left_x = round(player.x * TILE_SIZE - screen_rect.w / 2)
        top_left_y = round(player.y * TILE_SIZE - screen_rect.h / 2)

        chunks_coord = get_chunk_range(
            top_left_x // TILE_SIZE,
            top_left_y // TILE_SIZE,
            (top_left_x + screen_rect.w) // TILE_SIZE,
            (top_left_y + screen_rect.h) // TILE_SIZE)

        chunks = filter(None,
                        (self.context.object_store.get_chunk(*chunk_coord)
                         for chunk_coord in chunks_coord))
        entity_big_bag = set()

        for chunk in chunks:
            self.screen.blit(
                chunk.map.current_frame,
                (chunk.map.x * 15 * TILE_SIZE - top_left_x,
                 chunk.map.y * 15 * TILE_SIZE - top_left_y))
            entity_big_bag.add(chunk.entities)
        for entity_small_bag in entity_big_bag:
            for entity in entity_small_bag:
                if entity.sprite_name:
                    entity.sprite.update(self.context.dt)
                    self.screen.blit(entity.current_frame,
                                     (entity.x * TILE_SIZE - top_left_x,
                                      entity.y * TILE_SIZE - top_left_y))
                try:
                    for sprite, x_delta, y_delta in entity.additional_sprites:
                        self.screen.blit(
                            sprite,
                            (entity.x * TILE_SIZE - top_left_x + x_delta,
                             entity.y * TILE_SIZE - top_left_y + y_delta))
                except AttributeError:
                    pass

    def process_events(self):
        if not self.context.graphics:
            return
        for event in pygame.event.get():
            logger.trace('Got event: %s', event)
            kwargs = event.dict
            kwargs.update({'type': event.type, 'context': self.context})
            on_event.execute(kwargs)
