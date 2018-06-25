import tkinter as tk

from bakasable.debug.storeframe import StoreFrame


class PeerStoreFrame(StoreFrame):
    def create_widgets(self):
        super().create_widgets()

        self.object_info = tk.Text(
            self, wrap='word', state=tk.DISABLED)

        self.object_info.tag_configure('title', font=('Times', '14', 'bold'))
        self.object_info.pack(side='right', fill='both', expand=True)
