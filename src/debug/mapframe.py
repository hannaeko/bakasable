import tkinter as tk

import pygame
import PIL.Image
import PIL.ImageTk

from bakasable.entities import MapChunk
from bakasable.entities import mngt


class MapFrame(tk.Frame):
    def __init__(self, context, master=None):
        super().__init__(master)
        self.context = context
        self.create_widgets()
        self.chunks_img = {}
        self.after(500, self.update_map)

    def create_widgets(self):
        self.canvas = tk.Canvas(self)
        self.canvas.pack(fill='both', expand=True)

    def update_map(self):
        self.after(500, self.update_map)
        self.canvas.delete(tk.ALL)
        try:
            for entity in self.context.object_store.store.values():
                if isinstance(entity, MapChunk):
                    sprite = entity.get_sprite()
                    img_str = pygame.image.tostring(sprite, 'RGB')
                    rect = sprite.get_rect()
                    img = PIL.Image.frombytes('RGB', (rect.w, rect.h), img_str)
                    img.thumbnail((90, 90))

                    self.chunks_img[entity.uid] = PIL.ImageTk.PhotoImage(img)
                    self.canvas.create_image(
                        (self.canvas.winfo_width()//2+90*entity.x,
                         self.canvas.winfo_height()//2+90*entity.y),
                        image=self.chunks_img[entity.uid])
                    x = self.canvas.winfo_width()//2+90*entity.x-45
                    y = self.canvas.winfo_height()//2+90*entity.y-45
                    if entity.uid in self.context.object_store.coordinated:
                        self.canvas.create_rectangle(
                            x, y, x+90, y+90, fill='', outline='red')
                    if (entity.x, entity.y) in mngt.watched_chunks:
                        self.canvas.create_rectangle(
                            x, y, x+90, y+90, fill='',
                            outline='blue', dash=(10, 10))
        # store size changed, pass, will be computed next iteration
        except RuntimeError:
            pass
