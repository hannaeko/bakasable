import tkinter as tk

import pygame
import PIL.Image
import PIL.ImageTk


class MainWindow(tk.Frame):
    def __init__(self, context, master=None):
        super().__init__(master)
        self.master
        self.context = context
        self.pack(expand=True, fill='both')
        self.create_widgets()

    def create_widgets(self):
        self.entities_list_frame = tk.Frame(self)

        self.y_scroll = tk.Scrollbar(
            self.entities_list_frame, orient=tk.VERTICAL)
        self.y_scroll.pack(side='right', fill='y')

        self.x_scroll = tk.Scrollbar(
            self.entities_list_frame, orient=tk.HORIZONTAL)
        self.x_scroll.pack(side='bottom', fill='x')

        self.entities_list = tk.Listbox(
            self.entities_list_frame,
            xscrollcommand=self.x_scroll.set,
            yscrollcommand=self.y_scroll.set)

        self.entities_list.pack(
            side='left', fill='y', expand=True, anchor='nw')
        self.entities_list.bind(
            '<<ListboxSelect>>', self.update_selected_object)
        self.entities_list_frame.pack(
            side='left', fill='y', expand=False, anchor='nw')

        self.x_scroll['command'] = self.entities_list.xview
        self.y_scroll['command'] = self.entities_list.yview

        self.info_frame = tk.Frame(self)

        self.object_info = tk.Text(
            self.info_frame, wrap='word', state=tk.DISABLED)
        self.object_info.pack(side='left', fill='both', expand=True)

        self.sprite_frame = tk.Frame(self, width=200)
        self.sprite = tk.Label(self.sprite_frame)
        self.sprite.pack(expand=True)
        self.sprite_frame.pack_propagate(0)
        self.sprite_frame.pack(side='right', fill='y')

        self.object_info.tag_configure('title', font=('Times', '14', 'bold'))

        self.info_frame.pack(side='right', expand=True, fill='both')

    def update_objects_list(self, objects_ids):
        for id in objects_ids:
            obj = self.context.object_store.get(id, expend_chunk=False)
            self.entities_list.insert(
                tk.END, '%s#%d' % (type(obj).__name__, obj.uid))

    def display_object_info(self, obj):
        self.object_info.insert(
            tk.END, '%s#%d' % (type(obj).__name__, obj.uid), 'title')
        for key in obj.attr:
            self.object_info.insert(tk.END, getattr(obj, key))

    def update_selected_object(self, evt):
        selected = self.entities_list.curselection()
        if selected:
            value = self.entities_list.get(selected[0])
            uid = int(value.split('#')[1])
            entity = self.context.object_store.get(uid, expend_chunk=False)

            self.object_info['state'] = tk.NORMAL
            self.object_info.delete('1.0', tk.END)
            self.object_info.insert(
                tk.END, '%s\n' % value, 'title')
            for key in entity.attr:
                self.object_info.insert(
                    tk.END, '    \u25CF %s=%s\n' % (key, getattr(entity, key)))
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
