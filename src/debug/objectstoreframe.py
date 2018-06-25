import tkinter as tk

import pygame
import PIL.Image
import PIL.ImageTk

from bakasable.debug.storeframe import StoreFrame


class ObjectStoreFrame(StoreFrame):

    def create_widgets(self):
        super().create_widgets()

        self.object_info = tk.Text(
            self, wrap='word', state=tk.DISABLED)

        self.sprite_frame = tk.Frame(self, width=200)
        self.sprite = tk.Label(self.sprite_frame)
        self.sprite.pack(expand=True)
        self.sprite_frame.pack_propagate(0)
        self.sprite_frame.pack(side='right', fill='y')

        self.object_info.tag_configure('title', font=('Times', '14', 'bold'))
        self.object_info.pack(side='right', fill='both', expand=True)

    def id_to_value(self, uid):
        obj = self.context.object_store.get(uid, expend_chunk=False)
        return '%s#%d' % (type(obj).__name__, obj.uid)

    def value_to_id(self, value):
        return int(value.split('#')[1])

    def on_list_selected_change(self, evt):
        selected = self.list.curselection()
        if selected:
            value = self.list.get(selected[0])
            uid = int(value.split('#')[1])
            entity = self.context.object_store.get(uid, expend_chunk=False)

            self.object_info['state'] = tk.NORMAL
            self.object_info.delete('1.0', tk.END)
            self.object_info.insert(
                tk.END, '%s\n' % value, 'title')
            for key in entity.attr:
                self.object_info.insert(
                    tk.END, '    \u25CF %s=%s\n' % (key, getattr(entity, key)))

            coordinator = self.context.peer_store.get_closest_uid(uid)
            self.object_info.insert(tk.END, 'coordinator: %d' % coordinator)
            self.object_info['state'] = tk.DISABLED
            sprite = entity.get_sprite()
            if sprite:
                img_str = pygame.image.tostring(sprite, 'RGBA')
                rect = sprite.get_rect()
                img = PIL.Image.frombytes('RGBA', (rect.w, rect.h), img_str)
                img.thumbnail((200, 200))

                self.tk_img = PIL.ImageTk.PhotoImage(img)
                self.sprite['image'] = self.tk_img
                self.sprite.pack()
            else:
                self.sprite['image'] = ''
