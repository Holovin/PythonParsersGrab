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
