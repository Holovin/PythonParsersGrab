import os
from os.path import join, dirname, abspath
from dotenv import load_dotenv


class Config:
    loaded = False

    @staticmethod
    def load(file_name='../config/.env'):
        load_dotenv(join(dirname(__file__), file_name))
        env_file_path = abspath(join(dirname(__file__), '../config', os.environ.get('ENV_FILE')))

        if not os.path.exists(env_file_path):
            raise FileNotFoundError('Can''t find site config file')

        load_dotenv(env_file_path)
        Config.loaded = True

    @staticmethod
    def get(key):
        if Config.loaded is False:
            Config.load()

        value = os.environ.get(key)

        if value is None:
            raise ValueError('Empty config value, name {}'.format(key))

        return value

    @staticmethod
    def get_seq(key, sep='_'):
        if Config.loaded is False:
            Config.load()

        array = []
        counter = 1

        while True:
            value = os.environ.get('{}{}{}'.format(key, sep, counter))

            if value is None or counter > 1000:
                break

            array.append(value)
            counter += 1

        if len(array) == 0:
            raise ValueError('Empty seq values')

        return array

