import os
from os.path import join, dirname
from dotenv import load_dotenv


class Config:
    loaded = False

    @staticmethod
    def load(file_name='.env'):
        env_file_path = join(dirname(__file__), file_name)
        load_dotenv(env_file_path)
        Config.loaded = True

    @staticmethod
    def get(key):
        if Config.loaded is False:
            Config.load()

        value = os.environ.get(key)

        if value is None:
            raise ValueError('Empty config value')

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

