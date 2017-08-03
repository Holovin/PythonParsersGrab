import os
from dotenv import load_dotenv


class Config:
    max_seq_size = 1000
    loaded = False

    @staticmethod
    def load(config_dir, file_name):
        base_file_path = os.path.join(config_dir, '.env')
        if not load_dotenv(base_file_path):
            raise Exception('Base config not defined, path: {}'.format(base_file_path))

        site_file_path = os.path.join(config_dir, file_name)
        if not load_dotenv(site_file_path):
            raise Exception('Site config not defined, path: {}'.format(site_file_path))

        Config.loaded = True

    @staticmethod
    def get(key, default_value=None):
        value = os.environ.get(key)

        if not value:
            if default_value is not None:
                return default_value

            raise ValueError('Empty config value, name {}'.format(key))

        return value

    @staticmethod
    def get_seq(key, sep='_'):
        array = []
        counter = 1

        while True:
            value = os.environ.get('{}{}{}'.format(key, sep, counter))

            if value is None or counter > Config.max_seq_size:
                break

            array.append(value)
            counter += 1

        if len(array) == 0:
            raise ValueError('Empty seq values')

        return array

