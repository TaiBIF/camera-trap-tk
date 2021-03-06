import tkinter as tk
from tkinter import (
    ttk,
)

from tkinter import filedialog as fd
from tkinter.messagebox import showinfo

import threading

class FolderList(tk.Frame):

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.app = self.parent.app

        self.source_list = []

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=0)
        #self.grid_rowconfigure(4, weight=0)
        self.grid_columnconfigure(0, weight=0)

        add_button = ttk.Button(
            self,
            text='加入資料夾',
            command=self.add_folder,
            takefocus=0)
        add_button.grid(row=0, column=0, pady=4, sticky='n')

        separator = ttk.Separator(self, orient='horizontal')
        separator.grid(row=1, column=0, sticky='ew', pady=2)

        title = tk.Label(
            self,
            text='資料夾',
            font=tk.font.Font(family='Microsoft JhengHei', size=12),
            bg='#4f5d75')
        title.grid(row=2, column=0, padx=4, pady=4, sticky='nw')

        self.source_list_frame = tk.Frame(self, bg='#4f5d75')
        self.source_list_frame.grid(row=2, column=0, pady=4, sticky='n')

        #separator = ttk.Separator(self, orient='horizontal')
        #separator.grid(row=3, column=0, sticky='ew', pady=2)

        #upload_progress_button = ttk.Button(
        #    self,
        #    text='上傳進度',
        #    command=self.toggle_upload_progress)
        #upload_progress_button.grid(row=4, column=0, pady=4, sticky='s')


        #add_button = ttk.Button(
        #    self,
        #    text='看大圖',
        #    command=self.add_folder)
        #add_button.grid(pady=4)

        #self.image_sql_list = []

        self.refresh_source_list()

    # def toggle_upload_progress(self):
    #     main = self.app.main
    #     upload_progress = self.app.upload_progress
    #     if main.winfo_viewable():
    #         main.grid_remove()
    #         upload_progress.grid(row=2, column=1, sticky='nsew')
    #     else:
    #         upload_progress.grid_remove()
    #         main.grid(row=2, column=1, sticky='nsew')

    def refresh_source_list(self):
        db = self.app.db

        # reset source_list
        if a := self.source_list:
            for i in a:
                i.destroy()
            self.source_list = []

        # get all source from db
        res = db.fetch_sql_all('SELECT * FROM source')

        style = ttk.Style()
        style.configure('my.TButton', font=('Verdana', 9))

        for i in res:
            #print (i)
            '''
            folder_frame = tk.Frame(self.source_list_frame)
            folder_frame.grid(padx=4, pady=2, sticky='nw')

            title = ttk.Label(folder_frame, text=i[3], font=tk.font.Font(family='Microsoft JhengHei', size=13, weight='bold'))
            title.grid(row=0, column=0, sticky='nw')
            path = ttk.Label(folder_frame, text=i[2], font=tk.font.Font(family='Microsoft JhengHei', size=8))
            path.grid(row=1, column=0, sticky='nw')

            num = ttk.Label(folder_frame, text=f'{i[4]} 張照片', font=tk.font.Font(family='Microsoft JhengHei', size=10))
            num.grid(row=2, column=0, sticky='nw')
            '''
            uploaded_mark = '*' if i[6] == '40' else ''
            source_button = ttk.Button(
                self.source_list_frame,
                text=f'{i[3]}{uploaded_mark} ({i[4]})',
                style='my.TButton',
                takefocus=0,
                command=lambda x=i[0]: self.app.frames['main'].from_source(x))
            source_button.grid(padx=4, pady=2, sticky='nw')

            self.source_list.append(source_button)


    def insert_image_to_db(self, image_sql_list):
        for i in image_sql_list:
            self.app.db.exec_sql(i)
        self.app.db.commit()

        self.refresh_source_list()
        showinfo(message='完成匯入資料夾')

    def add_folder_worker(self, src, source_id, image_list, folder_path):
        self.app.frames['landing'].show(True)
        total = len(image_list)
        self.app.frames['landing'].render_progress_bar(
            length=400,
            title='製作縮圖中，請稍後 ...',
            sub_title1=f'目錄: {folder_path}')
        self.app.frames['landing'].progress_bar['maximum'] = total
        image_sql_list = []

        for i, v in enumerate(src.gen_import_image(source_id, image_list, folder_path)):
            #self.app.db.exec_sql(v[1])
            image_sql_list.append(v[1])
            self.app.frames['landing'].progress_bar['value'] = i+1
            self.app.frames['landing'].thumb_label['text'] = '{} ({}/{})'.format(image_list[i].name, i+1, total)
            #progress_bar['value'] = i+1
            #self.update_idletasks()

        #self.app.db.commit()
        #progress_bar['value'] = 0
        #self.update_idletasks()

        self.app.after(100, lambda: self.insert_image_to_db(image_sql_list))


    def add_folder(self):
        directory = fd.askdirectory()
        if not directory:
            return False

        src = self.app.source
        folder_path = src.get_folder_path(directory)

        if not folder_path:
            tk.messagebox.showinfo('info', '已經加過此資料夾')
            return False

        image_list = src.get_image_list(folder_path)

        source_id = src.create_import_directory(image_list, folder_path)
        threading.Thread(target=self.add_folder_worker, args=(src, source_id, image_list, folder_path)).start()
        #self.refresh_source_list()
        '''

        progress_bar = self.app.statusbar.progress_bar



        progress_bar['maximum'] = len(image_list)
        self.update_idletasks()

        source_id = src.create_import_directory(image_list, folder_path)
        threading.Thread(target=self.add_folder_worker, args=(src, source_id, image_list, folder_path)).start()
        #for i, v in enumerate(src.gen_import_image(source_id, image_list, folder_path)):
        #    self.app.db.exec_sql(v[1])
        #    progress_bar['value'] = i+1
        #    self.update_idletasks()

        #progress_bar['value'] = 0
        #self.update_idletasks()

        #self.refresh_source_list()
        '''
