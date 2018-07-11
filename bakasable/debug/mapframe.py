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
        self.canvas_obj_to_entity = {}
        self.after(500, self.update_map)

    def create_widgets(self):
        self.control_frame = tk.Frame(self)

        self.position_label = tk.Label(self.control_frame, text='x=0, y=0')
        self.position_label.pack(side='left')

        self.reset_pos_button = tk.Button(
            self.control_frame, text='Reset', command=self.reset_coord)
        self.reset_pos_button.pack(side='left')

        self.info_label = tk.Label(self.control_frame)
        self.info_label.pack(side='left')

        self.control_frame.pack(fill='x', expand=True)

        self.canvas = tk.Canvas(self, background='black')
        self.canvas.pack(fill='both', expand=True)

        self.canvas.bind('<ButtonPress-1>', self.scroll_start)
        self.canvas.bind('<B1-Motion>', self.scroll_move)
        self.canvas.tag_bind('object', '<Motion>', self.display_object_info)

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

    def display_object_info(self, event):
        obj_id = self.canvas.find_closest(event.x, event.y)[0]
        entity = self.canvas_obj_to_entity.get(obj_id, None)
        if entity:
            self.info_label['text'] = str(entity.uid)

    def update_map(self):
        self.after(500, self.update_map)
        self.canvas.delete(tk.ALL)
        self.canvas_obj_to_entity.clear()
        try:
            for entity in self.context.object_store.store.values():
                if isinstance(entity, MapChunk):
                    img_str = pygame.image.tostring(
                        entity.current_frame, 'RGB')
                    rect = entity.current_frame.get_rect()
                    img = PIL.Image.frombytes('RGB', (rect.w, rect.h), img_str)
                    img.thumbnail((90, 90))

                    self.chunks_img[entity.uid] = PIL.ImageTk.PhotoImage(img)

                    x = self.canvas.winfo_width() // 2 + 90 * entity.x
                    y = self.canvas.winfo_height() // 2 + 90 * entity.y

                    obj_id = self.canvas.create_image(
                        (x + 45, y + 45),
                        image=self.chunks_img[entity.uid],
                        tag=('map', 'object'))

                    if entity.uid in self.context.object_store.coordinated:
                        self.canvas.create_rectangle(
                            x, y, x+90, y+90, fill='',
                            outline='red', tag='info')

                    if (entity.x, entity.y) in mngt.watched_chunks:
                        self.canvas.create_rectangle(
                            x, y, x+90, y+90, fill='',
                            outline='blue', dash=(10, 10), tag='info')
                else:
                    x = self.canvas.winfo_width() // 2 + 6 * entity.x
                    y = self.canvas.winfo_height() // 2 + 6 * entity.y

                    if entity.uid in self.context.object_store.coordinated:
                        color = 'red'
                    elif not entity.active:
                        color = 'lightgray'
                    else:
                        color = 'orange'

                    obj_id = self.canvas.create_rectangle(
                        x-5, y-5,  x+5, y+5,
                        fill=color, tag=('entity', 'object'))
                self.canvas_obj_to_entity[obj_id] = entity
            try:
                self.canvas.tag_raise('entity', 'map')
                self.canvas.tag_raise('info', 'object')
            # tagOrId "map" doesn't match any items
            except tk.TclError:
                pass
        # store size changed, pass, will be computed next iteration
        except RuntimeError:
            pass
