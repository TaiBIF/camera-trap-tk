import json
import time
import tkinter as tk
from tkinter import ttk
from logging import debug as _d
from logging import info as _i
from PIL import ImageTk, Image

#import threading

from helpers import (
    FreeSolo,
    TreeHelper,
    DataHelper,
)
from image import check_thumb
from tkdatagrid import DataGrid



#from tkintertable.Testing import sampledata
#DATA=sampledata()
#print (DATA)
class Worker:
    finished = False
    def do_work(self):
        time.sleep(10)
        self.finished=True
    def start(self):
        self.th = threading.Thread(target=self.do_work)
        self.th.start()


class Main(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)

        #self.parent = parent
        self.app = parent

        self.source_data = {}
        self.projects = self.app.server.projects
        self.id_map = {
            'project': {},
            'studyarea': {},
            'deployment': {},
            'sa_to_d': {}
        }
        self.id_map['project'] = {x['name']: x['project_id'] for x in self.projects}

        self.source_id = None
        self.current_row = 0
        self.thumb_basewidth = 500

        self.tree_helper = TreeHelper()
        self.data_helper = DataHelper()
        self.annotation_entry_list = []

        # layout
        #self.grid_propagate(False)
        self.layout()
        #self.config_ctrl_frame()
        #self.config_table_frame()

    def handle_panedwindow_release(self, event):
        w = self.right_frame.winfo_width()
        # border: 8, padx: 10
        self.thumb_basewidth = w - 36
        data = self.get_current_item('data')

        if data:
            self.show_thumb(data['thumb'], data['path'])
        elif self.tree_helper.data:
            # when default no selection
            self.show_thumb(self.tree_helper.data[0]['thumb'], self.tree_helper.data[0]['path'])

    def layout(self):
        '''
           left_frame        right_frame
        +================================+
        |  ctrl_frame     | +----------+ |
        +-----------------+ |thumbnail | |
        |                 | |          | |
        |  table_frame    | +----------+ |
        |                 |  annotation  |
        |                 |              |
        +=================|==============+
        '''
        self.grid_rowconfigure(0, weight=0) # fix
        self.grid_columnconfigure(0, weight=1)

        #panedwindow_style = ttk.Style()
        self.panedwindow = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        #panedwindow_style = configure('PanedWindow', sashpad=5)
        self.panedwindow.pack(fill=tk.BOTH, expand=True)
        self.panedwindow.grid_rowconfigure(0, weight=1)
        self.panedwindow.grid_columnconfigure(0, weight=1)
        self.panedwindow.bind("<ButtonRelease-1>", self.handle_panedwindow_release)
        self.right_frame = tk.Frame(self.panedwindow, bg='#2d3142')
        self.left_frame = tk.Frame(self.panedwindow)
        #self.right_frame = tk.Frame(self.panedwindow, bg='brown')

        self.panedwindow.add(self.left_frame)
        self.panedwindow.add(self.right_frame)

        # layout: left frame
        self.left_frame.grid_rowconfigure(0, weight=0) # fix
        self.left_frame.grid_rowconfigure(1, weight=1) # expand vertical
        self.left_frame.grid_columnconfigure(0, weight=1)

        self.ctrl_frame = tk.Frame(self.left_frame)
        self.table_frame = tk.Frame(self.left_frame)

        self.ctrl_frame.grid(row=0, column=0, sticky='we')
        self.table_frame.grid(row=1, column=0, sticky='news')

        self.config_ctrl_frame()
        self.config_table_frame()

        # layout: right frame
        self.right_frame.grid_rowconfigure(0, weight=0)
        self.right_frame.grid_rowconfigure(1, weight=0)
        self.right_frame.grid_columnconfigure(0, weight=1)

        # thumb
        self.image_thumb_frame = tk.Frame(self.right_frame, bg='#ef8354')
        self.image_thumb_frame.grid(row=0, column=0, sticky='nswe')

        self.image_thumb = ttk.Label(self.image_thumb_frame, border=8, relief='raised')
        self.image_thumb.grid(row=0, column=0, sticky='nw', padx=10, pady=10)

        ### annotation
        self.annotation_label_frame = ttk.LabelFrame(self.right_frame, text="影像標注")
        self.annotation_label_frame.grid(row=1, column=0, sticky='nw', padx=10, pady=10)

        self.annotation_label_frame.grid_rowconfigure(0, weight=0)
        self.annotation_label_frame.grid_rowconfigure(1, weight=0)
        self.annotation_label_frame.grid_columnconfigure(0, weight=0)
        self.annotation_label_frame.grid_columnconfigure(1, weight=0)
        self.annotation_label_frame.grid_columnconfigure(2, weight=0)

        species_label = ttk.Label(
            self.annotation_label_frame,
            text='物種')
        species_label.grid(row=0, column=0, sticky='we', pady=(6, 0))
        self.species_value = tk.StringVar()
        #self.species_entry = ttk.Entry(
        #    self.annotation_label_frame,
        #    textvariable=self.species_value
        #)
        sp_choices = self.app.config.get('AnnotationFieldSpecies', 'choices').split(',')
        self.species_free = FreeSolo(
            self.annotation_label_frame,
            sp_choices,
            value=self.species_value,
        )
        self.species_free.grid(row=1, column=0, padx=4)
        self.annotation_entry_list.append((self.species_free, self.species_value))

        lifestage_label = ttk.Label(
            self.annotation_label_frame,
            text='年齡')
        lifestage_label.grid(row=0, column=1, sticky='we', pady=(6, 0))
        self.lifestage_value = tk.StringVar()
        ls_choices = self.app.config.get('AnnotationFieldLifeStage', 'choices').split(',')
        self.lifestage_free = FreeSolo(
            self.annotation_label_frame,
            ls_choices,
            value=self.lifestage_value,
        )
        self.lifestage_free.grid(row=1, column=1, padx=4)
        self.annotation_entry_list.append((self.lifestage_free, self.lifestage_value))

        sex_label = ttk.Label(
            self.annotation_label_frame,
            text='性別')
        sex_label.grid(row=0, column=2, sticky='we', pady=(6, 0))
        self.sex_value = tk.StringVar()
        sx_choices = self.app.config.get('AnnotationFieldSex', 'choices').split(',')
        self.sex_free = FreeSolo(
            self.annotation_label_frame,
            sx_choices,
            value=self.sex_value,
        )
        self.sex_free.grid(row=1, column=2, padx=4)
        self.annotation_entry_list.append((self.sex_free, self.sex_value))

        antler_label = ttk.Label(
            self.annotation_label_frame,
            text='角況')
        antler_label.grid(row=2, column=0, sticky='we', pady=(6, 0))
        self.antler_value = tk.StringVar()
        an_choices = self.app.config.get('AnnotationFieldAntler', 'choices').split(',')
        self.antler_free = FreeSolo(
            self.annotation_label_frame,
            an_choices,
            value=self.antler_value,
        )
        self.antler_free.grid(row=3, column=0, padx=4)
        self.annotation_entry_list.append((self.antler_free, self.antler_value))

        remark_label = ttk.Label(
            self.annotation_label_frame,
            text='備註')
        remark_label.grid(row=2, column=1, sticky='we', pady=(6, 0))
        self.remark_value = tk.StringVar()
        self.remark_entry = ttk.Entry(
            self.annotation_label_frame,
            textvariable=self.remark_value
        )
        self.remark_entry.grid(row=3, column=1, padx=4)
        self.annotation_entry_list.append((self.remark_entry, self.remark_value))

        animal_id_label = ttk.Label(
            self.annotation_label_frame,
            text='個體 ID')
        animal_id_label.grid(row=2, column=2, sticky='we', pady=(6, 0))
        self.animal_id_value = tk.StringVar()
        self.animal_id_entry = ttk.Entry(
            self.annotation_label_frame,
            textvariable=self.animal_id_value
        )
        self.animal_id_entry.grid(row=3, column=2, padx=4)
        self.annotation_entry_list.append((self.animal_id_entry, self.animal_id_value))

        # append keyboard navigation
        self.species_free.bind('<Up>', self.move_key)
        self.species_free.bind('<Down>', self.move_key)
        self.lifestage_free.bind('<Up>', self.move_key)
        self.lifestage_free.bind('<Down>', self.move_key)
        self.sex_free.bind('<Up>', self.move_key)
        self.sex_free.bind('<Down>', self.move_key)
        self.antler_free.bind('<Up>', self.move_key)
        self.antler_free.bind('<Down>', self.move_key)
        self.species_free.bind('<FocusOut>', self.fo_species)
        self.lifestage_free.bind('<FocusOut>', self.fo_lifestage)
        self.sex_free.bind('<FocusOut>', self.fo_sex)
        self.antler_free.bind('<FocusOut>', self.fo_antler)
        annotation_update_button = ttk.Button(
            self.annotation_label_frame,
            text='存檔',
            command=self.update_annotation,
        )
        annotation_update_button.grid(row=4, column=0, padx=16, pady=16)
        annotation_clone_button = ttk.Button(
            self.annotation_label_frame,
            text='複製一列',
            command=self.clone_row
        )
        annotation_clone_button.grid(row=4, column=1, padx=12, pady=12)
        #self._show_thumb()

        # self.image_viewer_button = ttk.Button(
        #     self.table_frame,
        #     text='看大圖',
        #     command=lambda: self.app.main.show_frame('image-viewer')
        # )

        #self.image_viewer_button.grid(row=1, column=1, sticky='n')

    def fo_species(self, event):
        #print (self.species_free.listbox, event)
        if self.species_free.listbox:
            self.species_free.handle_update(event)

    def fo_lifestage(self, event):
        if self.lifestage_free.listbox:
            self.lifestage_free.handle_update(event)

    def fo_sex(self, event):
        if self.sex_free.listbox:
            self.sex_free.handle_update(event)

    def fo_antler(self, event):
        if self.antler_free.listbox:
            self.antler_free.handle_update(event)

    def config_ctrl_frame(self):
        self.ctrl_frame.grid_rowconfigure(0, weight=0)
        self.ctrl_frame.grid_rowconfigure(1, weight=0)
        self.ctrl_frame.grid_columnconfigure(0, weight=0)
        self.ctrl_frame.grid_columnconfigure(1, weight=0)
        self.ctrl_frame.grid_columnconfigure(2, weight=0)
        self.ctrl_frame.grid_columnconfigure(3, weight=0)
        self.ctrl_frame.grid_columnconfigure(4, weight=0)
        self.ctrl_frame.grid_columnconfigure(5, weight=0)
        self.ctrl_frame.grid_columnconfigure(6, weight=0)
        self.ctrl_frame.grid_columnconfigure(7, weight=0)
        self.ctrl_frame.grid_columnconfigure(8, weight=0)

        self.ctrl_frame2 = tk.Frame(self.ctrl_frame)
        self.ctrl_frame2.grid_rowconfigure(0, weight=0)
        self.ctrl_frame2.grid_columnconfigure(0, weight=0)
        self.ctrl_frame2.grid(row=1, column=0, sticky='we', columnspan=6)
        # folder
        self.label_folder = ttk.Label(
            self.ctrl_frame,
            text='',
            font=tk.font.Font(family='Helvetica', size=18, weight='bold'))
        self.label_folder.grid(row=0, column=0, padx=(0, 36))

        # project menu
        self.label_project = ttk.Label(self.ctrl_frame,  text='計畫')
        self.label_project.grid(row=0, column=1)
        self.project_options = [x['name'] for x in self.projects]
        self.project_var = tk.StringVar(self)
        self.project_menu = tk.OptionMenu(
            self.ctrl_frame,
            self.project_var,
            '-- 選擇計畫 --',
            *self.project_options,
            command=self.project_option_changed)
        self.project_menu.grid(row=0, column=2, sticky=tk.W, padx=(6, 16))

        # studyarea menu
        self.label_studyarea = ttk.Label(self.ctrl_frame,  text='樣區')
        self.label_studyarea.grid(row=0, column=3)
        self.studyarea_var = tk.StringVar()
        self.studyarea_options = []
        self.studyarea_menu = tk.OptionMenu(
            self.ctrl_frame,
            self.studyarea_var,
            '')
        self.studyarea_var.trace('w', self.studyarea_option_changed)
        self.studyarea_menu.grid(row=0, column=4, sticky=tk.W,padx=(6, 20))

        # deployment menu
        self.label_deployment = ttk.Label(self.ctrl_frame,  text='相機位置')
        self.label_deployment.grid(row=0, column=5)
        self.deployment_options = []
        self.deployment_var = tk.StringVar(self.ctrl_frame)
        self.deployment_var.trace('w', self.deployment_option_changed)
        self.deployment_menu = tk.OptionMenu(
            self.ctrl_frame,
            self.deployment_var,
            '')
        self.deployment_menu.grid(row=0, column=6, sticky=tk.W, padx=(6, 20))

        # upload button
        self.upload_button = ttk.Button(
            self.ctrl_frame,
            text='上傳',
            command=self.handle_upload)
        self.upload_button.grid(row=0, column=7, padx=20, sticky='w')

        self.delete_button = ttk.Button(
            self.ctrl_frame,
            text='刪除資料夾',
            command=self.handle_delete)
        self.delete_button.grid(row=0, column=8, padx=5, sticky='e')

        # image sequence
        self.seq_checkbox_val = tk.StringVar(self)
        self.seq_checkbox = ttk.Checkbutton(
            self.ctrl_frame2,
            text='連拍分組',
	    command=self.refresh,
            variable=self.seq_checkbox_val,
	    onvalue='Y',
            offvalue='N')
        self.seq_checkbox.grid(row=0, column=0, padx=(4, 10))

        self.seq_interval_val = tk.StringVar(self)
        #self.seq_interval_val.trace('w', self.on_seq_interval_changed)
        self.seq_interval_entry = ttk.Entry(
            self.ctrl_frame2,
            textvariable=self.seq_interval_val,
            width=4,
            #validate='focusout',
            #validatecommand=self.on_seq_interval_changed
        )
        self.seq_interval_entry.bind(
            "<KeyRelease>", lambda _: self.refresh())
        self.seq_interval_entry.grid(row=0, column=1)

        self.seq_unit = ttk.Label(self.ctrl_frame2,  text='分鐘 (相鄰照片間隔__分鐘，顯示分組)')
        self.seq_unit.grid(row=0, column=2)

    def config_table_frame(self):
        self.table_frame.grid_columnconfigure(0, weight=2)
        self.table_frame.grid_columnconfigure(1, weight=0)
        self.table_frame.grid_rowconfigure(0, weight=2)
        self.table_frame.grid_rowconfigure(1, weight=0)
        #print (self.table_frame.grid_info(), self.table_frame.grid_bbox())

        #self.message = ttk.Label(self.table_frame, text="Hello", width=50)
        #self.message.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)

        # treeview
        #print (self.source_data['image_list'])
        self.data_grid = DataGrid(self.table_frame, data={}, columns=self.data_helper.columns)
        self.data_grid.grid(row=0, column=0, sticky='nsew')
        '''
        self.tree = ttk.Treeview(
            self.table_frame,
            columns=[x[0] for x in self.tree_helper.heading],
            show='tree headings')

        self.tree.column('#0', width=40, stretch=False)
        for i in self.tree_helper.heading:
            self.tree.heading(i[0], text=i[1])
            self.tree.column(i[0], **i[2])

        self.tree.bind('<<TreeviewSelect>>', self.handle_select)
        #self.tree.bind('<<TreeviewOpen>>', self.select_open)
        #self.tree.bind('<<TreeviewClose>>', self.select_close)
        #self.tree.bind('<ButtonRelease-1>', self.on_click)

        self.tree.grid(row=0, column=0, sticky='nsew')

        scrollbar_x = ttk.Scrollbar(self.table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        scrollbar_y = ttk.Scrollbar(self.table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(
            xscroll=scrollbar_x.set,
            yscroll=scrollbar_y.set
        )
        scrollbar_x.grid(row=1, column=0, sticky='ew')
        scrollbar_y.grid(row=0, column=1, sticky='ns')

        # tree style
        tree_style = ttk.Style()
        tree_style.configure("Treeview", font=("微軟正黑體", 10))
        #style_value.configure("Treeview", rowheight=30, font=("微軟正黑體", 10))
        tree_style.map(
            "Treeview",
            foreground=self.tree_helper.fixed_map(tree_style, "foreground"),
            background=self.tree_helper.fixed_map(tree_style, "background"))
        '''

    def from_source(self, source_id=None):
        self.app.begin_from_source()

        self.source_id = source_id
        self.source_data = self.app.source.get_source(self.source_id)
        if descr := self.source_data['source'][7]:
            d = json.loads(descr)
            # set init value
            self.project_var.set(d.get('project_name', ''))
            self.studyarea_var.set(d.get('studyarea_name', ''))
            self.deployment_var.set(d.get('deployment_name', ''))
        else:
            self.project_var.set('')
            self.studyarea_var.set('')
            self.deployment_var.set('')
        self.refresh()

        # default show first image
        '''
        self.show_thumb(self.tree_helper.data[0]['thumb'], self.tree_helper.data[0]['path'])
        '''

    def refresh(self):
        # get source_data
        #print ('refresh, main: get source', self.source_id, from_source)
        #if self.source_id and from_source == True:
        #    self.from_source(source_id)

        data = self.data_helper.read_image_list(self.source_data['image_list'])
        self.data_grid.refresh(data)
        '''
        self.tree.delete(*self.tree.get_children())

        tree_data = self.tree_helper.set_data_from_list(self.source_data['image_list'])

        self.seq_info = None
        if self.seq_checkbox_val.get() == 'Y':
            if seq_int := self.seq_interval_val.get():
                self.seq_info = self.tree_helper.group_image_sequence(seq_int, seq_tag='tag_name')

        if self.seq_info:
            for i, values in enumerate(tree_data):
                data = self.tree_helper.data[i]
                tag = data['tag_name']
                iid = data['iid']
                parent = data['iid_parent']
                text = data['counter']
                self.tree.insert(parent, tk.END, iid, text=text, values=values, tags=(tag), open=True)
            for tag_name, item in self.seq_info['map'].items():
                self.tree.tag_configure(tag_name, background=item['color'])
        else:
            for i, values in enumerate(tree_data):
                data = self.tree_helper.data[i]
                iid = data['iid']
                parent = data['iid_parent']
                text = data['counter']
                if i%2 == 0:
                    self.tree.insert(parent, tk.END, iid, values=values, tags=('even',), text=text, open=True)
                else:
                    self.tree.insert(parent, tk.END, iid, values=values, tags=('odd',), text=text, open=True)
            self.tree.tag_configure('odd', background='#E8E8E8')
            self.tree.tag_configure('even', background='#DFDFDF')
        '''
        # folder name
        self.label_folder['text'] = self.source_data['source'][3]

    def project_option_changed(self, *args):
        name = self.project_var.get()
        id_ = self.id_map['project'].get(name,'')
        # reset
        self.studyarea_options = []
        self.id_map['studyarea'] = {}
        self.id_map['deployment'] = {}
        self.id_map['sa_to_d'] = {}

        res = self.app.server.get_projects(id_)
        for i in res['studyareas']:
            self.id_map['studyarea'][i['name']] = i['studyarea_id']
            self.studyarea_options.append(i['name'])

            if i['name'] not in self.id_map['sa_to_d']:
                self.id_map['sa_to_d'][i['name']] = []
            for j in i['deployments']:
                self.id_map['sa_to_d'][i['name']].append(j)
                self.id_map['deployment'][j['name']] = j['deployment_id']
        # refresh
        #print (self.studyarea_options)
        #print (self.id_map['studyarea'], self.id_map['deployment'])
        # refresh studyarea_options
        self.studyarea_var.set('-- 選擇樣區 --')
        menu = self.studyarea_menu['menu']
        menu.delete(0, 'end')
        for sa_name in self.studyarea_options:
            menu.add_command(label=sa_name, command=lambda x=sa_name: self.studyarea_var.set(x))

    def studyarea_option_changed(self, *args):
        selected_sa = self.studyarea_var.get()
        self.deployment_options = []
        for i in self.id_map['sa_to_d'].get('selected_sa', []):
            self.deployment_options.append(i['name'])
        # refresh studyarea_options
        self.deployment_var.set('-- 選擇相機位置 --')
        menu = self.deployment_menu['menu']
        menu.delete(0, 'end')
        for d in self.id_map['sa_to_d'].get(selected_sa, []):
            menu.add_command(label=d['name'], command=lambda x=d['name']: self.deployment_var.set(x))

    def deployment_option_changed(self, *args):
        d_name = self.deployment_var.get()
        if deployment_id := self.id_map['deployment'].get(d_name, ''):
            #print ('set deployment_id: ', deployment_id, d_name, )
            sa_name = self.studyarea_var.get()
            p_name = self.project_var.get()
            descr = {
                'deployment_id': deployment_id,
                'deployment_name': d_name,
                'studyarea_id': self.id_map['studyarea'].get(sa_name, ''),
                'studyarea_name': sa_name,
                'project_id': self.id_map['project'].get(p_name, ''),
                'project_name': p_name,
            }
            #print (descr)

            # save to db
            sql = "UPDATE source SET description='{}' WHERE source_id={}".format(json.dumps(descr), self.source_id)
            _i('change deployment) %s'%sql)
            self.app.db.exec_sql(sql, True)

            # update source_data (for upload: first time import folder, get no deployment_id even if selected)
            self.source_data = self.app.source.get_source(self.source_id)
            # TODO
            #tk.messagebox.showinfo('info', '已設定相機位置')

    def handle_upload(self):
        #self.app.source.do_upload(self.source_data)
        ans = tk.messagebox.askquestion('上傳確認', '確定要上傳?')
        if ans == 'no':
            return False

        image_list = self.source_data['image_list']
        source_id = self.source_data['source'][0]
        deployment_id = ''

        if descr := self.source_data['source'][7]:
            d = json.loads(descr)
            deployment_id = d.get('deployment_id', '')

        if deployment_id == '':
            tk.messagebox.showinfo('info', '末設定相機位置，無法上傳')
            return False

        pb = self.app.statusbar.progress_bar
        start_val = len(image_list) * 0.05 # 5% for display pre s3 upload
        pb['maximum'] = len(image_list) + start_val
        pb['value'] = start_val
        self.update_idletasks()

        res = self.app.source.upload_annotation(image_list, source_id, deployment_id)

        if res['error']:
            tk.messagebox.showerror('上傳失敗', f"{res['error']}")
            return False

        saved_image_ids = res['data']
        for i, v in enumerate(self.app.source.gen_upload_file(image_list, source_id, deployment_id, saved_image_ids)):
            print ('uploaded', i, v)
            if v:
                # update progress bar
                pb['value'] = i+1
                self.update_idletasks()

                local_image_id = v[0]
                server_image_id = v[1]
                s3_key = v[2]
                sql = 'UPDATE image SET upload_status="200", server_image_id={} WHERE image_id={}'.format(server_image_id, local_image_id)
                self.app.db.exec_sql(sql, True)

                # update server image status
                self.app.server.post_image_status({
                    'file_url': s3_key,
                    'pk': server_image_id,
                })

        # finish upload
        pb['value'] = 0
        self.update_idletasks()
        tk.messagebox.showinfo('info', '上傳成功')

    def handle_delete(self):
        ans = tk.messagebox.askquestion('確認', f"確定要刪除資料夾: {self.source_data['source'][3]}?")
        if ans == 'no':
            return False

        self.app.source.delete_folder(self.source_id)
        self.app.sidebar.refresh_source_list()
        self.app.show_landing()

    # DEPRICATED
    def save_tree_to_db(self):
        print ('save to db')
        a_conf = self.tree_helper.get_conf('annotation')
        ts_now = int(time.time())
        for iid in self.tree.get_children():
            record = self.tree.item(iid, 'values')
            d = {x[1][0]: record[x[0]] for x in a_conf}

            row = int(iid[3:])
            item = self.tree_helper.data[row]
            image_id = item['image_id']
            print (iid, image_id, item)
            if image_id:
                sql = "UPDATE image SET annotation='[{}]', changed={} WHERE image_id={}".format(json.dumps(d), ts_now, image_id)
                #print (sql)
                #self.app.db.exec_sql(sql)

        #self.app.db.commit()
        #tk.messagebox.showinfo('info', '儲存成功')

    def get_status_display(self, code):
        status_map = {
            '10': 'new',
            '20': 'viewed',
            '30': 'annotated',
            '100': 'start',
            '110': '-',
            '200': 'uploaded',
        }
        return status_map.get(code, '-')

    def get_current_item(self, cat='data'):
        sel = self.tree.selection()
        if len(sel) <= 0:
            return None

        iid = sel[0]
        #text = self.tree.item(selected_item, 'text')
        if cat == 'data':
            return self.tree_helper.get_data(iid)

    def handle_select(self, event):
        iid = ''
        record = None
        for selected_item in self.tree.selection():
            #print ('select first: ', selected_item)
            #values = self.tree.item(selected_item, 'values')
            iid = selected_item
            record = self.tree.item(selected_item, 'values')
            #self.current_row = int(text)

            break
        #print ('select)', iid)
        if iid:
            row = self.tree_helper.get_data(iid)
            self.show_thumb(row['thumb'], row['path'])

            # set viewed
            if st := row.get('status', 0):
                if int(st) < 20:
                    sql = "UPDATE image SET status='20' where image_id={}".format(row['image_id'])
                    self.app.db.exec_sql(sql, True)
                    values = list(record)
                    values[0] = values[0].replace('new', 'viewed')
                    self.tree.item(iid, values=values)
                    # refresh cause blink and slow
                    #self.from_source(self.source_id)
                    #self.tree.focus(iid)
                    #self.tree.selection_set(iid)

            self.begin_edit_annotation(iid)

    def begin_edit_annotation(self, iid):
        record = self.tree.item(iid, 'values')
        a_conf = self.tree_helper.get_conf('annotation')
        for i, v in enumerate(self.annotation_entry_list):
            a_index = a_conf[i][0]
            v[1].set(record[a_index])
            if a_conf[i][1][3]['widget'] == 'freesolo':
                if v[0].listbox:
                    v[0].remove_listbox()

        # set first entry focus
        #self.annotation_entry_list([0][0].focus()) # not work ?
        # !!
        #print (self.annotation_entry_list[0][0].set_focus())

    def show_thumb(self, thumb_path, image_path):
        real_thumb_path = check_thumb(thumb_path, image_path)
        image = Image.open(real_thumb_path)
        # aspect ratio
        basewidth = self.thumb_basewidth
        wpercent = (basewidth/float(image.size[0]))
        hsize = int((float(image.size[1])*float(wpercent)))
        img = image.resize((basewidth, hsize))
        #img = image.resize((300,300))
        #img = image.resize((300,300), Image.ANTIALIAS)
        photo = ImageTk.PhotoImage(img)
        self.image_thumb.configure(image=photo)
        self.image_thumb.image = photo
        self.update_idletasks()

    def _get_alist(self, iid, iid_parent):
        annotation_iid = iid if iid_parent == '' else iid_parent
        row = self.tree_helper.get_data(annotation_iid)
        return row.get('alist', [])

    def update_annotation(self):
        '''update to tree and save'''
        is_selected_parent = False
        a_conf = self.tree_helper.get_conf('annotation')
        ts_now = int(time.time())
        entry_dict = self.tree_helper.get_annotation_dict(self.annotation_entry_list)

        for iid in self.tree.selection():
            seq_name = ''
            if tag_list := self.tree.item(iid, 'tag'):
                seq_tag_list= [x for x in tag_list if 'tag' in x]
                if seq_tag_list:
                    seq_name = seq_tag_list[0]

            row = self.tree_helper.get_data(iid)
            if row['iid_parent'] == '':
                is_selected_parent = True
            alist = self._get_alist(iid, row['iid_parent'])
            annotation_index = int(iid.split(':')[2])
            if len(alist) > 0:
                alist[annotation_index] = entry_dict
            else:
                alist = [entry_dict]

            # update selected
            sql = "UPDATE image SET annotation='{}', status='30', changed={} WHERE image_id={}".format(json.dumps(alist), ts_now, row['image_id'])
            #print ('update annotation:', sql)
            self.app.db.exec_sql(sql)

            index_list = []
            # only work while select parent and enable seq_info
            if is_selected_parent == True and self.seq_info and seq_name != '':
                index_list = self.seq_info['map'][seq_name]['rows']
            for x in index_list:
                has_parent = self.tree_helper.data[x]['iid_parent']
                if not has_parent:
                    related_image_id = self.tree_helper.data[x]['image_id']
                    if related_image_id != row['image_id']:
                        # set alist
                        foo_iid = self.tree_helper.data[x]['iid']
                        alist = self._get_alist(foo_iid, self.tree_helper.data[x]['iid_parent'])
                        annotation_index = int(foo_iid.split(':')[2])
                        if len(alist) > 0:
                            alist[annotation_index] = entry_dict
                        else:
                            alist = [entry_dict]
                            
                        sql = "UPDATE image SET annotation='{}', status='30', changed={} WHERE image_id={}".format(json.dumps(alist), ts_now, related_image_id)
                        self.app.db.exec_sql(sql)
                        #print ('update annotation (image_seq):', sql)

            self.app.db.commit()


        for a in self.annotation_entry_list:
            a[1].set('')

        self.from_source(self.source_id)

    def clone_row(self):
        source_iid = ''
        for iid in self.tree.selection():
            record = self.tree.item(iid, 'values')
            source_iid = iid # clone only get first
            break

        row = self.tree_helper.get_data(source_iid)
        alist = self._get_alist(source_iid, row['iid_parent'])
        a_index = int(iid.split(':')[2])
        cloned_annotation = {}
        if len(alist) > 0:
            alist.append(alist[a_index])
        else:
            alist = [{},{}]

        ts_now = int(time.time())
        sql = "UPDATE image SET annotation='{}', changed={} WHERE image_id={}".format(json.dumps(alist), ts_now, row['image_id'])
        #print ('clone annotation:', sql)
        #_i('sql:%s'%sql)
        self.app.db.exec_sql(sql, True)
        #self.refresh()
        self.from_source(self.source_id)

    def move_key(self, event):
        #print ('move_key', event)
        if event.keysym == 'Down':
            self.move_selection('next')
        elif event.keysym == 'Up':
            self.move_selection('prev')

    def move_selection(self, action):
        for selected_item in self.tree.selection():
            iid = selected_item

            row = self.tree_helper.get_data(iid)
            data = self.tree_helper.data
            break

        if not row or len(data) <= 0:
            return False

        if current := row['counter']:
            #print ('from', iid, current)
            move_to = None
            if action == 'next':
                if current < len(data):
                    move_to = data[current]['iid']
                    #move_to = main.tree.next(next_iid)
            elif action == 'prev':
                if current > 0:
                    move_to = data[current-2]['iid']
                    #move_to = main.tree.prev(iid)
            #print ('to', move_to)
            # tk.treeview next & prev need to consider children
            if move_to:
                self.tree.focus(move_to)
                #main.tree.focus_set() # cause double action
                self.tree.selection_set(move_to)
