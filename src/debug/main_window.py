import tkinter as tk
from tkinter import ttk

from bakasable.debug.objectstoreframe import ObjectStoreFrame
from bakasable.debug.peerstoreframe import PeerStoreFrame
from bakasable.debug.mapframe import MapFrame
from bakasable.debug.generalinfoframe import GeneralInfoFrame


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
        self.map_frame = MapFrame(self.context, self.tabs)
        self.tabs.add(self.map_frame, text='World map')
        self.general_info_frame = GeneralInfoFrame(self.context, self.tabs)
        self.tabs.add(self.general_info_frame, text='General Info')
