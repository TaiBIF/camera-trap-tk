import tkinter as tk
from tkinter import (
    ttk,
)
from PIL import (
    Image,
    ImageTk
)

from image import aspect_ratio


class HelpPage(tk.Frame):

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.app = parent

        self.layout()

    def handle_mouse_wheel(self, event):
        # print(event) # TODO
        if event.num == 5 or event.delta == -120:
            self.yview_scroll(1, 'units')
            self.canvas.yview_scroll(1, 'units')
        elif event.num == 4 or event.delta == 120:
            if self.canvasy(0) < 0:  # ?
                return
            self.yview_scroll(-1, 'units')
            self.canvas.yview_scroll(-1, 'units')

    def handle_yviews(self, *args):
        self.canvas.yview(*args)

    def layout(self):
        self.grid_rowconfigure(0, weight=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        self.scrollbar_y = ttk.Scrollbar(
            self,orient=tk.VERTICAL,
            command=self.handle_yviews)
        self.scrollbar_y.grid(row=0, column=1, sticky='news',pady=0, ipady=0)


        img = Image.open('./assets/help-content.png')
        to_size = aspect_ratio(img.size, width=self.app.app_width)
        self.photo = ImageTk.PhotoImage(img.resize(to_size))
        self.canvas = tk.Canvas(
            self,
            width=self.app.app_width,
            height=self.app.app_height-50-25,
            bg='#CFCFCF',
            bd=0,
            highlightthickness=0,
            relief='ridge',
            scrollregion=(0, 0, to_size[0], to_size[1]),
            yscrollcommand=self.scrollbar_y.set,
        )
        self.canvas.grid(row=0, column=0, sticky='ewns')

        self.canvas.bind('<MouseWheel>', self.handle_mouse_wheel)

        # self.canvas.create_text(
        #     250,
        #     80,
        #     text='~ 教學內容 ~',
        #     font=('Arial', 40),
        #     fill=self.app.app_primary_color,
        # )

        self.canvas.create_image(
            0,
            0,
            image=self.photo,
            anchor='nw',
        )


