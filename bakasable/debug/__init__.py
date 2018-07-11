import tkinter as tk
import threading

from bakasable.debug.main_window import MainWindow


class DebugTool(threading.Thread):
    def __init__(self, context):
        threading.Thread.__init__(self)
        self.daemon = True
        self.context = context
        self.start()

    def callback(self):
        if not self.context.graphics:
            self.context.carry_on = False

    def update_set(self, all_ids, cb):
        current_ids = self.ids_registry.get(cb, set())
        old_ids = current_ids - all_ids
        new_ids = all_ids - current_ids
        cb(new_ids, old_ids)
        self.ids_registry[cb] = all_ids

    def update_window(self):
        self.root.after(100, self.update_window)

        self.update_set(
            set(self.context.peer_store.keys()),
            self.app.peer_store_frame.update_list)

        if self.app.object_store_frame.filter_coordinated.get():
            self.update_set(
                set(self.context.object_store.coordinated),
                self.app.object_store_frame.update_list)
        else:
            self.update_set(
                set(self.context.object_store.store.keys()),
                self.app.object_store_frame.update_list)

    def run(self):
        self.root = tk.Tk()
        self.root.protocol('WM_DELETE_WINDOW', self.callback)
        self.root.geometry('800x300')
        self.root.title('Debug Tool - %d' % self.context.peer_id)
        self.root.resizable(0, 0)
        self.root.after(100, self.update_window)

        self.ids_registry = {}
        self.objects_ids = set()
        self.peers_ids = set()

        self.app = MainWindow(self.context, master=self.root)
        self.root.mainloop()
