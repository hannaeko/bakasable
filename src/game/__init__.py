import pygame


class Game:
    def __init__(self, context):
        self.context = context
        self.screen = pygame.display.set_mode((800, 600))

    def loop(self):
        pygame.display.flip()

        # TODO: get screen size/player coordinate
        # TODO: compute list of visible chunk
        # TODO: fetch those chunk (map + entities)
        # TODO: for each chunk display map then display entities

        # simple code to test display and chunk sprite generation.
        for object in self.context.object_store.store.values():
            if object.sprite is not None:
                self.screen.blit(object.sprite, (0, 0))
