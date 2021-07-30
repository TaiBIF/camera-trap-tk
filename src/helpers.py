import tkinter as tk
from tkinter import ttk

from pathlib import Path
import json
from datetime import datetime
import random
import colorsys

HEADER = {
    'status_display': {
        'label': '標注/上傳狀態',
        'width': 100,
        'type': 'text',
    },
    'thumb': {
        'label': '照片',
        'width': 55,
        'type': 'image',
    },
    'filename': {
        'label': '檔名',
        'width': 150,
        'type': 'text',
    },
    'datetime_display': {
        'label': '日期時間',
        'width': 130,
        'type': 'text',
    },
    'annotation_species': {
        'label': '物種',
        'width': 80,
    },
    'annotation_lifestage': {
        'label': '年齡',
        'width': 80
    },
    'annotation_sex': {
        'label': '性別',
        'width': 80
    },
    'annotation_antler': {
        'label': '角況',
        'width': 80
    },
    'annotation_remark': {
        'label': '性別',
        'width': 80
    },
    'annotation_animal_id': {
        'label': '個體ID',
        'width': 80
    }
}

def _get_status_display(code):
    status_map = {
        '10': 'new',
        '20': 'viewed',
        '30': 'annotated',
        '100': 'start',
        '110': '-',
        '200': 'uploaded',
    }
    return status_map.get(code, '-')


class DataHelper(object):
    def __init__(self, db):
        #self.annotation_item = [4, 5, 6, 7, 8, 9] # index from sqlite
        self.db = db
        self.annotation_map = {
            4: 'annotation_species',
            5: 'annotation_lifestage',
            6: 'annotation_sex',
            7: 'annotation_antler',
            8: 'annotation_remark',
            9: 'annotation_animal_id'
        } #[4, 5, 6, 7, 8, 9] # index from sqlite
        self.data = {}
        self.columns = HEADER
        self.img_seq_rand_salt = random.random()
        self.annotation_data = {}
        #self.current_index = 0

    def save_annotation(self, iid, key, value, seq_info=None):
        iid_root = None
        iid_index = None
        if '-' in iid:
            iid_list = iid.split('-')
            iid_root = iid_list[0]
            a_index = int(iid_list[1]) + 1
            item = self.data[iid_root]
        else:
            item = self.data[iid]
            iid_root = item['iid_root']
            a_index = int(item['a_index'])

        key = key.replace('annotation_', '')
        image_id = item['image_id']
        adata = self.annotation_data[iid_root]
        #print (self.annotation_data, a_index, key)
        if len(adata) <= int(a_index):
            adata.append({})
        adata[a_index][key] = value
        json_data = json.dumps(adata)

        if seq_info:
            if tag_name := item['img_seq_tag_name']:
                image_list = []
                for row in seq_info['map'][tag_name]['rows']:
                    x = self.get_item(row)
                    image_list.append(x['image_id'])
                image_list_set = set(image_list)
                rs = ','.join(str(x) for x in image_list_set)
                sql = f"UPDATE image SET status='30', annotation='{json_data}' WHERE image_id IN ({rs})"
                self.db.exec_sql(sql, True)
        else:
            sql = f"UPDATE image SET status='30', annotation='{json_data}' WHERE image_id={image_id}"
            self.db.exec_sql(sql, True)


    def read_image_list(self, image_list):
        '''
        iid rule: `iid:{image_index}-{annotation_index}`
        '''
        self.data = {}
        counter = 0
        for i_index, i in enumerate(image_list):
            image_id = i[0]
            alist = json.loads(i[7])
            self.annotation_data[f'{counter}'] = alist
            status_display = '{} / {}'.format(
                _get_status_display(i[5]),
                _get_status_display(i[12]),
            )
            thumb = f'./thumbnails/{i[10]}/{Path(i[2]).stem}-q.jpg'
            row_basic = {
                'status_display': status_display,
                'filename': i[2],
                'datetime_display': str(datetime.fromtimestamp(i[3])),
                'image_id': image_id,
                'path': i[1],
                'status': i[5],
                'upload_status': i[12],
                'time': i[3],
                'seq': 0,
                'sys_note': json.loads(i[13]),
                'thumb': thumb,
            }

            if len(alist) >= 1:
                for a_index, a in enumerate(alist):
                    row_multi = {
                        'counter': counter,
                        'a_index': a_index,
                        'iid_root': f'{i_index}',
                    }
                    for _, a_key in self.annotation_map.items():

                        k = a_key.replace('annotation_', '')
                        row_multi[a_key] = a.get(k, '')

                    #if len(alist) == 1:
                    #self.data[f'{}'] = {**row_basic, **row_multi}
                    #    else:
                    self.data[f'{counter}'] = {**row_basic, **row_multi}
                    counter += 1
            else:
                row_multi = {
                    'counter': counter,
                    'a_index': 0,
                    'iid_root': f'{i_index}',
                }
                for a_index, a_key in self.annotation_map.items():
                    row_multi[a_key] = ''
                self.data[f'{counter}'] = {**row_basic, **row_multi}
                counter += 1
        return self.data

    def get_item(self, row):
        for counter, row_key in enumerate(self.data.keys()):
            if row == counter:
                return self.data[row_key]

    def group_image_sequence(self, time_interval, seq_tag=''):
        seq_info = {
            'group_prev': False,
            'group_next': False,
            'map': {},
            'idx': 0,
            'salt': self.img_seq_rand_salt,
            'int': int(time_interval) * 60,
        }
        # via: https://martin.ankerl.com/2009/12/09/how-to-create-random-colors-programmatically/
        golden_ratio_conjugate = 0.618033988749895

        for counter, (i, v) in enumerate(self.data.items()):
            tag_name = ''
            next_idx = min(counter+1, len(self.data)-1)
            this_time = self.data[i]['time']
            next_time = self.data[str(next_idx)]['time'] if counter < next_idx else 0
            #print (i, this_time, next_time,(next_time - this_time), seq_info['int'])
            seq_info['group_prev'] = seq_info['group_next']
            if next_time and \
               (next_time - this_time) <= seq_info['int']:
                seq_info['group_next'] = True
            else:
                seq_info['group_next'] = False

            if seq_info['group_next'] == True and not seq_info['group_prev']:
                seq_info['idx'] += 1
                seq_info['salt'] += golden_ratio_conjugate
                seq_info['salt'] %= 1

            if seq_info['group_next'] or seq_info['group_prev']:
                tag_name = 'tag{}'.format(seq_info['idx'])
            else:
                tag_name = ''

            rgb_hex = ''
            if tag_name:
                rgb = colorsys.hls_to_rgb(seq_info['salt']*265, 0.8, 0.5)
                rgb_hex = f'#{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}'
                #print (i, tag_name, seq_info['idx'])
                if tag_name not in seq_info['map']:
                    seq_info['map'][tag_name] = {
                        'color': rgb_hex,
                        'rows': []
                    }
                seq_info['map'][tag_name]['rows'].append(counter)

            self.data[i]['img_seq_tag_name'] = tag_name
            self.data[i]['img_seq_color'] = rgb_hex
        #print (seq_info)
        return seq_info
'''
key, label, type, choices in ini
'''

HEADING = (
    #('index', '#',
    # {'width': 25, 'stretch': False}),
    ('status_display', '標注/上傳狀態',
     {'width': 40, 'stretch': False}),
    ('filename', '檔名',
     {'width': 120, 'stretch': False}),
    ('datetime_display','日期時間',
     {'width': 120, 'stretch': False}),
    ('annotation_species', '物種',
     {'width': 80, 'stretch': False},
     {'widget': 'freesolo',
      'config_section': 'AnnotationFieldSpecies'}),
    ('annotation_lifestage', '年齡',
     {'width': 50, 'stretch': False},
     {'widget': 'freesolo',
      'config_section': 'AnnotationFieldLifeStage'}),
    ('annotation_sex', '性別',
     {'width': 50, 'stretch': False},
     {'widget': 'freesolo',
      'config_section': 'AnnotationFieldSex'}),
    ('annotation_antler', '角況',
     {'width': 50, 'stretch': False},
     {'widget': 'freesolo',
      'config_section': 'AnnotationFieldAntler'}),
    ('annotation_remark', '備註',
     {'width': 50, 'stretch': False},
     {'widget': 'entry',
          'config_section': 'AnnotationFieldRemarks'}),
    ('annotation_animal_id', '個體 ID',
     {'width': 50, 'stretch': False},
     {'widget': 'entry',
      'config_section': 'AnnotationFieldAnimalID'}),
)

class TreeHelper(object):
    def __init__(self):
        self.heading = HEADING
        self.annotation_item = [3, 4, 5, 6, 7, 8]
        self.data = []
        self.current_index = 0

    def get_annotation_dict(self, entry_list):
        d = {}
        for i, v in enumerate(self.annotation_item):
            key = self.heading[v][0]
            key = key.replace('annotation_', '')
            d[key] = entry_list[i][1].get()

        return d

    def set_data(self, iid, alist):
        for i, v in enumerate(self.data):
            if v['iid'] == iid:
                self.data[i]['alist'] = alist
        #print (self.data)
        #found = self.get_data(iid)

    def get_data(self, iid):
        return list(filter(lambda x: x['iid'] == iid, self.data))[0]

    def get_conf(self, cat='annotation'):
        '''
        return [(index, conf)...]
        '''
        #return list(filter(lambda x: x[0] == key, self.conf))[0] or None
        if cat == 'annotation':
            return [(x, self.heading[x]) for x in self.annotation_item]

    def set_data_from_list(self, image_list):
        '''
        iid rule: `iid:{image_index}:{annotation_index}`
        '''
        rows = []
        counter = 0
        for i_index, i in enumerate(image_list):
            alist = json.loads(i[7])
            status_display = '{} / {}'.format(
                _get_status_display(i[5]),
                _get_status_display(i[12]),
            )
            thumb = f'./thumbnails/{i[10]}/{Path(i[2]).stem}-l.jpg'
            row_basic = {
                'status_display': status_display,
                'filename': i[2],
                'datetime_display': str(datetime.fromtimestamp(i[3])),
                'image_id': i[0],
                'path': i[1],
                'status': i[5],
                'upload_status': i[12],
                'time': i[3],
                'seq': 0,
                'sys_note': json.loads(i[13]),
                'thumb': thumb,
            }

            if len(alist) >= 1:
                for a_index, a in enumerate(alist):
                    counter += 1
                    row_multi = {
                        'counter': counter,
                        'iid': f'iid:{i_index}:{a_index}',
                        'iid_parent': '',
                        'alist': [],
                    }
                    for head_index in self.annotation_item:
                        key = self.heading[head_index][0]
                        k = key.replace('annotation_', '')
                        row_multi[key] = a.get(k, '')

                    if a_index == 0:
                        row_multi['alist'] = alist
                    else:
                        row_multi['iid_parent'] = f'iid:{i_index}:0'

                    rows.append({**row_basic, **row_multi})
            else:
                counter += 1
                row_multi = {
                    'counter': counter,
                    'iid': 'iid:{}:0'.format(i_index),
                    'iid_parent': '',
                    'alist': alist,
                }
                for head_index in self.annotation_item:
                    key = self.heading[head_index][0]
                    row_multi[key] = ''
                rows.append({**row_basic, **row_multi})

        self.data = rows
        tree_data = []
        for i in rows:
            values = [i.get(h[0], '')
                      for h_index, h in enumerate(self.heading)]
            #print (i['iid'], i.get('iid_parent', ''))
            #print (values)
            tree_data.append(values)

        return tree_data

    def group_image_sequence(self, time_interval, highlight='', seq_tag=''):
        seq_info = {
            'group_prev': False,
            'group_next': False,
            'map': {},
            'idx': 0,
            'salt': random.random(),
            'int': int(time_interval) * 60,
        }
        # via: https://martin.ankerl.com/2009/12/09/how-to-create-random-colors-programmatically/
        golden_ratio_conjugate = 0.618033988749895

        for i, v in enumerate(self.data):
            tag_name = ''
            next_idx = min(i+1, len(self.data)-1)
            this_time = self.data[i]['time']
            next_time = self.data[next_idx]['time'] if i < next_idx else 0
            #print (i, this_time, next_time,(next_time - this_time), seq_info['int'])
            seq_info['group_prev'] = seq_info['group_next']
            if next_time and \
               (next_time - this_time) <= seq_info['int']:
                seq_info['group_next'] = True
            else:
                seq_info['group_next'] = False

            if seq_info['group_next'] == True and not seq_info['group_prev']:
                seq_info['idx'] += 1
                seq_info['salt'] += golden_ratio_conjugate
                seq_info['salt'] %= 1

            if seq_info['group_next'] or seq_info['group_prev']:
                tag_name = 'tag{}'.format(seq_info['idx'])
            else:
                tag_name = ''

            rgb_hex = ''
            if tag_name:
                rgb = colorsys.hls_to_rgb(seq_info['salt']*265, 0.8, 0.5)
                rgb_hex = f'#{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}'
                #print (i, tag_name, seq_info['idx'])
                if tag_name not in seq_info['map']:
                    seq_info['map'][tag_name] = {
                        'color': rgb_hex,
                        'rows': []
                    }
                seq_info['map'][tag_name]['rows'].append(i)

            if highlight:
                v[highlight] = rgb_hex
            if seq_tag:
                v[seq_tag] = tag_name

        #print (seq_info)
        return seq_info

    # via: https://stackoverflow.com/questions/56331001/python-tkinter-treeview-colors-are-not-updating
    def fixed_map(self, style, option):
        # Returns the style map for 'option' with any styles starting with
        # ("!disabled", "!selected", ...) filtered out

        # style.map() returns an empty list for missing options, so this should
        # be future-safe
        return [elm for elm in style.map("Treeview", query_opt=option)
                if elm[:2] != ("!disabled", "!selected")]




def data_to_tree_values(data):
    rows = []
    for i in data:
        values = [i.get(h[0], '')for h in HEADING]
        rows.append(values)
    return rows

def image_list_to_table(image_list):
    rows = []
    counter = 0
    for i in image_list:
        alist = json.loads(i[7])
        path = i[1]
        status_display = '{} / {}'.format(
            _get_status_display(i[5]),
            _get_status_display(i[12]),
        )
        basic_item = {
            'status_display': status_display,
            'filename': i[2],
            'datetime_display': str(datetime.fromtimestamp(i[3])),
        }
        ctrl_item = {
            'image_id': i[0],
            'path': i[1],
            'status': i[5],
            'upload_status': i[12],
            'time': i[3],
            'seq': 0,
        }
        if len(alist) >= 1:
            for j in alist:
                counter += 1
                basic_item['index'] = counter
                annotation_item = {
                    'species': j.get('species', ''),
                    'lifestage': j.get('lifestage', ''),
                    'sex': j.get('sex', ''),
                    'antler':j.get('antler', ''),
                    'animal_id':j.get('animal_id', ''),
                    'remarks': j.get('remarks', ''),
                }
                rows.append({
                    **basic_item,
                    **annotation_item,
                    **ctrl_item,
                })
        else:
            counter += 1
            annotation_item = {
                'species': '',
                'lifestage': '',
                'sex': '',
                'antler': '',
                'animal_id': '',
                'remarks': '',
            }
            rows.append({
                **basic_item,
                **annotation_item,
                **ctrl_item,
            })
    return rows


class FreeSolo(ttk.Entry, object):
    def __init__(
            self,
            parent,
            choices=None,
            value=None,
            entry_args={},
            listbox_args={},
    ):
        #autocomplete_function=None, , ignorecase_match=False, startswith_match=True, vscrollbar=True, hscrollbar=True, value_callback=None, **kwargs):
        self.choices = choices
        self.filtered_choices = []
        self.listbox_frame = None

        if not value:
            entry_args['textvariable'] = tk.StringVar()
        else:
            self.value = entry_args['textvariable'] = value

        default_listbox_args = {
            'width': None,
            'height': 9,
            'background': 'white',
            'selectmode': tk.SINGLE,
            'activestyle': 'none',
            'exportselection': False,
        }
        self.listbox_args = {**default_listbox_args, **listbox_args}

        ttk.Entry.__init__(
            self,
            parent,
            **entry_args)

        self.value_trace_id = self.value.trace('w', self.handle_trace)
        self.bind('<Return>', self.handle_update) # next?
        self.bind('<Escape>',  self.handle_update)
        #self.bind('<Down>', lambda event: self.create_listbox())
        #self.bind('<Return>', lambda _: self.create_listbox())
        self.bind('<Return>', self.toggle_listbox)
        #self.bind("<FocusOut>", lambda _: self.remove_listbox()) # will cause listbox gone!
        #self.bind('<FocusOut>', self.haldel_update)

        self.listbox = None
        #self.build_listbox()

    #def set_value(self, value, close_listbox=False):
        #self._entry_var.trace_vdelete("w", self._trace_id)
        #self._entry_var.set(text)
        #self._trace_id = self._entry_var.trace('w', self._on_change_entry_var)
    #    self.value.set(value)
    #    if close_listbox:
    #        self.close_listbox()

    def test(self, e):
        print ('test', e, self.listbox, self)

    def set_focus(self):
        self.focus()

    def handle_trace(self, name, index, mode):
        val = self.value.get()
        #print ('free trace', val)
        #if val == '':
        #    #self.focus() # ?
        #else:
        if val:
            filtered = [i for i in self.choices if i.startswith(val)]
            #print ('filtered:', filtered, self.listbox)
            if len(filtered) > 0:
                if self.listbox is None:
                    self.create_listbox(filtered)
                else:
                    self.listbox.delete(0, tk.END)
                    for i in filtered:
                        self.listbox.insert(tk.END, i)

    def handle_update(self, event):
        #print ('handle_update')
        if listbox := self.listbox:
            current_selection = listbox.curselection()
            if current_selection:
                text = listbox.get(current_selection)
                self.value.set(text)


        # destroy listbox
        self.remove_listbox()

        self.focus()
        self.icursor(tk.END)
        self.xview_moveto(1.0)

    def toggle_listbox(self, event):
        #if not self.list_box_frame:
        #    self
        #if not self.listbox_frame:
        #    self.listbox_frame = tk.Frame()

        if not self.listbox:
            self.create_listbox()
        else:
            print ('pass')

    def create_listbox(self, filtered_choices=[]):
        #print (self.listbox, 'create', self.listbox_frame)
        self.listbox_frame = tk.Frame()
        self.listbox = tk.Listbox(self.listbox_frame, **self.listbox_args)
        self.listbox.grid(row=0, column=0, sticky = 'news')

        self.listbox.bind("<ButtonRelease-1>", self.handle_update)
        #        self.listbox.bind("<Return>", self._update_entry)
        #self.listbox.bind("<Escape>", lambda _: self.unpost_listbox())

        self.listbox_frame.grid_columnconfigure(0, weight= 1)
        self.listbox_frame.grid_rowconfigure(0, weight= 1)

        #x = -self.cget("borderwidth") - self.cget("highlightthickness")
        x = 0
        #y = self.winfo_height()-self.cget("borderwidth") - self.cget("highlightthickness")
        y = self.winfo_height()

        if self.listbox_args.get('width', ''):
            width = self.listbox_width
        else:
            width = self.winfo_width()
        #print (x, y, width, self.winfo_height(),self.cget("borderwidth"),self.cget("highlightthickness"))
        y = 22
        width = 120
        self.listbox_frame.place(in_=self, x=x, y=y, width=width)

        #self.update_listbox_choices(filtered_choices)

        #def update_listbox_choices(self, filtered_choices=[]):
        #print ('update list', filtered_choices)

        choices = filtered_choices if len(filtered_choices) else self.choices
        for i in choices:
            self.listbox.insert(tk.END, i)

            #height = min(self._listbox_height, len(values))
            #        self._listbox.configure(height=height)

    def remove_listbox(self):
        if self.listbox is not None:
            #print (self.listbox.master, 'master')
            self.listbox.master.destroy()
            self.listbox = None

    def terminate(self):
        self.remove_listbox()
        self.value.set('')
        self.destroy()
