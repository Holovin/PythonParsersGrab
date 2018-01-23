# data_saver.py
# Module for save data as single JSON/CSV or separated as some JSON/CSV files
# r4

import logging
import time

from abc import ABC, abstractmethod

logger = logging.getLogger('ddd_site_parse')


class DataSaver(ABC):
    def __init__(self, params: {}):
        self.data = []

        self.output_dir = params.get('output_dir')
        self.output_file_name = params.get('output_file', time.strftime('%d_%m_%Y'))
        self.encoding = params.get('encoding', 'utf8')
        self.ext = ''

    def set_data(self, data) -> None:
        self.data = data

    def get_file_name(self, name: str, *args: str) -> str:
        if name == '':
            name = self.output_file_name

        additional = ''

        for arg in args:
            additional += '_{}'.format(arg)

        return '{}{}.{}'.format(name, additional, self.ext)

    @abstractmethod
    def save(self, data_fields: [], params: {}):
        pass

    @abstractmethod
    def save_by_category(self, data_fields: [], category_field: str, params: {}):
        pass

    @staticmethod
    def fix_row_encoding(row: {}, encoding: str, mode: str='replace'):
        for field in row.keys():
            row[field] = row[field].encode(encoding, mode).decode(encoding)
