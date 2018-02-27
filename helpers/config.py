# config.py
# Config loader, wrapper around load_dotenv lib functions
# r2

import os
from dotenv import load_dotenv


class Config:
    max_seq_size = 50
    loaded = False

    @staticmethod
    def load(config_dir: str, file_name: str) -> None:
        base_file_path = os.path.join(config_dir, '.env')
        if not load_dotenv(base_file_path):
            raise Exception('Base config not defined, path: {}'.format(base_file_path))

        site_file_path = os.path.join(config_dir, file_name)
        if not load_dotenv(site_file_path):
            raise Exception('Site config not defined, path: {}'.format(site_file_path))

        Config.loaded = True

    @staticmethod
    def get(key: str, default_value: str = None) -> str:
        value = os.environ.get(key)

        if value is None:
            if default_value is not None:
                return default_value

            raise ValueError('Empty config value, name {}'.format(key))

        return value

    @staticmethod
    def get_seq(key: str, sep: str = '_') -> []:
        array = []
        counter = 1

        while True:
            value = os.environ.get('{}{}{}'.format(key, sep, counter))

            if value is None or counter > Config.max_seq_size:
                break

            array.append(value)
            counter += 1

        if len(array) == 0:
            raise ValueError('Empty seq values [key = {}]'.format(key))

        return array

    @staticmethod
    def get_dict(key_1: str, key_2: str, sep: str = '_', default_value: dict = None) -> dict:
        out_dict = {}
        counter = 1

        while True:
            key = os.environ.get('{}{}{}'.format(key_1, sep, counter))
            value = os.environ.get('{}{}{}'.format(key_2, sep, counter))

            if key is None or value is None or counter > Config.max_seq_size:
                break

            out_dict[key] = value
            counter += 1

        if len(out_dict) == 0:
            if default_value is not None:
                return default_value

            raise ValueError('Empty dict values')

        return out_dict
