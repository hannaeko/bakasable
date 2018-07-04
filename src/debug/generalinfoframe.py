import tkinter as tk


class GeneralInfoFrame(tk.Frame):
    def __init__(self, context, master=None):
        super().__init__(master)
        self.context = context
        self.create_widgets()
        self.pack()

    def create_widgets(self):
        self.tps_label = tk.Label(master=self)
        self.tps_label.pack(anchor='nw')
        self.update_tps()

    def update_tps(self):
        self.after(200, self.update_tps)
        try:
            self.tps_label['text'] = 'TPS = %.1f' % (1000/self.context.dt)
        except AttributeError:
            pass
