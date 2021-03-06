import configparser
import os

class Config(configparser.ConfigParser):
    ini_file = None

    def __init__(self, ini_file='config.ini'):
        super().__init__()

        self.ini_file = ini_file
        # copy sample if init_file not exists
        if not os.path.exists(self.ini_file):
            self.cp_sample()

        self.read(self.ini_file, encoding='utf-8')

    def cp_sample(self):
        init_sample_path = '{}.sample'.format(self.ini_file)
        with open(init_sample_path, encoding='utf-8') as f:
            sample_data = f.read()
            f.close()
            with open(self.ini_file, 'w', encoding='utf-8') as f_init:
                f_init.write(sample_data)
                f_init.close()


