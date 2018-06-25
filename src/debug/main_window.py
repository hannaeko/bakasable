import tkinter as tk
from tkinter import ttk

from bakasable.debug.objectstoreframe import ObjectStoreFrame
from bakasable.debug.peerstoreframe import PeerStoreFrame


class MainWindow(tk.Frame):
    def __init__(self, context, master=None):
        super().__init__(master)
        self.context = context
        self.create_widgets()
        self.pack()

    def create_widgets(self):
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(expand=True, fill='both')
        self.object_store_frame = ObjectStoreFrame(self.context, self.tabs)
        self.tabs.add(self.object_store_frame, text='Object store')
        self.peer_store_frame = PeerStoreFrame(self.context, self.tabs)
        self.tabs.add(self.peer_store_frame, text='Peer store')
