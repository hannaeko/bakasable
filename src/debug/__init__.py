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
        pass

    def update_window(self):
        self.root.after(100, self.update_window)

        all_obj_ids = set(self.context.object_store.store.keys())
        new_obj_ids = all_obj_ids - self.objects_ids
        new_obj_ids = all_obj_ids - self.objects_ids

        self.app.object_store_frame.update_list(new_obj_ids, set())
        self.objects_ids = all_obj_ids

        all_peer_ids = set(self.context.peer_store.keys())
        old_peer_ids = self.peers_ids - all_peer_ids
        new_peer_ids = all_peer_ids - self.peers_ids

        self.app.peer_store_frame.update_list(new_peer_ids, old_peer_ids)
        self.peers_ids = all_peer_ids

    def run(self):
        self.root = tk.Tk()
        self.root.protocol('WM_DELETE_WINDOW', self.callback)
        self.root.geometry('800x300')
        self.root.title('Debug Tool')
        self.root.resizable(0, 0)
        self.root.after(100, self.update_window)

        self.objects_ids = set()
        self.peers_ids = set()

        self.app = MainWindow(self.context, master=self.root)
        self.root.mainloop()
