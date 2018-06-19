import pygame

from bakasable.logic.chunk import get_chunk_range
from bakasable.const import TILE_SIZE


class Game:
    def __init__(self, context):
        self.context = context
        if self.context.graphics:
            self.screen = pygame.display.set_mode((800, 600))
            pygame.display.set_caption('Bakasable')
        else:
            self.screen = pygame.Surface((800, 600))

    def loop(self):
        if self.context.graphics:
            pygame.display.flip()

        player = self.context.object_store.get(self.context.peer_id)
        if not player:
            return

        screen_rect = self.screen.get_rect()

        top_left_x = round(player.x - screen_rect.w / 2)
        top_left_y = round(player.y - screen_rect.h / 2)

        chunks_coord = get_chunk_range(
            top_left_x // TILE_SIZE,
            top_left_y // TILE_SIZE,
            (top_left_x + screen_rect.w) // TILE_SIZE,
            (top_left_y + screen_rect.h) // TILE_SIZE)

        chunks = filter(None,
                        (self.context.object_store.get_chunk(*chunk_coord)
                         for chunk_coord in chunks_coord))

        for chunk in chunks:
            self.screen.blit(
                chunk.map.sprite,
                (chunk.map.x * 15 * TILE_SIZE - top_left_x,
                 chunk.map.y * 15 * TILE_SIZE - top_left_y))

            for entity in chunk.entities:
                sprite = entity.get_sprite()
                if sprite:
                    self.screen.blit(sprite,
                                     (entity.x * TILE_SIZE - top_left_x,
                                      entity.y * TILE_SIZE - top_left_y))