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
        self.control_frame = tk.Frame(self)
        self.position_label = tk.Label(self.control_frame, text='x=0, y=0')
        self.position_label.pack(side='left')
        self.reset_pos_button = tk.Button(
            self.control_frame, text='Reset', command=self.reset_coord)
        self.reset_pos_button.pack(side='left')
        self.control_frame.pack(fill='x', expand=True)
        self.canvas = tk.Canvas(self, background='black')
        self.canvas.pack(fill='both', expand=True)
        self.canvas.bind("<ButtonPress-1>", self.scroll_start)
        self.canvas.bind("<B1-Motion>", self.scroll_move)

    def scroll_start(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def scroll_move(self, event):
        self.position_label['text'] = 'x=%d, y=%d' % (
            self.canvas.canvasx(0), self.canvas.canvasy(0))
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def reset_coord(self):
        self.canvas.scan_mark(0, 0)
        self.canvas.scan_dragto(int(self.canvas.canvasx(0)),
                                int(self.canvas.canvasy(0)),
                                gain=1)
        self.position_label['text'] = 'x=0, y=0'

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
                        (self.canvas.winfo_width()//2+90*entity.x+45,
                         self.canvas.winfo_height()//2+90*entity.y+45),
                        image=self.chunks_img[entity.uid])
                    x = self.canvas.winfo_width()//2+90*entity.x
                    y = self.canvas.winfo_height()//2+90*entity.y
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
