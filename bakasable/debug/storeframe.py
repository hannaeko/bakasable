import tkinter as tk


class StoreFrame(tk.Frame):
    def __init__(self, context, master=None):
        super().__init__(master)
        self.context = context
        self.pack(expand=True, fill='both')
        self.create_widgets()

    def create_widgets(self):
        self.list_frame = tk.Frame(self)

        self.y_scroll = tk.Scrollbar(
            self.list_frame, orient=tk.VERTICAL)
        self.y_scroll.pack(side='right', fill='y')

        self.x_scroll = tk.Scrollbar(
            self.list_frame, orient=tk.HORIZONTAL)
        self.x_scroll.pack(side='bottom', fill='x')

        self.list = tk.Listbox(
            self.list_frame,
            xscrollcommand=self.x_scroll.set,
            yscrollcommand=self.y_scroll.set)

        self.list.pack(side='bottom', fill='y', expand=True)

        self.list.bind(
            '<<ListboxSelect>>', self.on_list_selected_change)
        self.list_frame.pack(
            side='left', fill='y', expand=False, anchor='nw')

        self.x_scroll['command'] = self.list.xview
        self.y_scroll['command'] = self.list.yview

    def update_list(self, new_ids, old_ids):
        if old_ids:
            for uid in old_ids:
                for index, value in enumerate(self.list.get(0, tk.END)):
                    list_uid = self.value_to_id(value)
                    if list_uid == uid:
                        self.list.delete(index)
                        break

        for uid in new_ids:
            self.list.insert(tk.END, self.id_to_value(uid))

    def on_list_selected_change(self, evt):
        pass

    def id_to_value(self, uid):
        return str(uid)

    def value_to_id(self, value):
        return int(value)
