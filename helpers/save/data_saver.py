# data_saver.py
# Module for save data as single JSON/CSV or separated as some JSON/CSV files
# r4

import logging
import time
import os

from abc import ABC, abstractmethod
from helpers.save.get_script_directory import get_script_directory

logger = logging.getLogger('ddd_site_parse')


class DataSaver(ABC):
    def __init__(self, params: {}):
        self.data = []

        self.output_dir = params.get('output_dir')
        self.output_file_name = params.get('output_file', time.strftime('%d_%m_%Y'))
        self.encoding = params.get('encoding', 'utf-8')
        self.ext = ''

    def set_data(self, data) -> None:
        self.data = data

    def get_file_name(self, name: str, sub_dir: str = None, *args: str) -> str:
        if name == '':
            name = self.output_file_name

        if sub_dir:
            name = os.path.join(sub_dir, name)

        additional = ''

        for arg in args:
            additional += f'_{arg}'

        filename = f'{name}{additional}.{self.ext}'
        filename_counter = 1

        while os.path.isfile(os.path.join(self._get_save_dir(filename))):
            filename = f'{name}{additional}_({filename_counter}).{self.ext}'
            filename_counter += 1

        return filename

    def save(self, data_fields: [], params: {}) -> None:
        if self._check_data():
            self._save(self.data, data_fields, self.get_file_name(''), {})

    def save_by_category(self, data_fields: [], category_field: str, params: {}) -> None:
        if self._check_data():
            result = {}

            # sep data
            for row in self.data:
                # create cat array
                if row[category_field] not in result:
                    result[row[category_field]] = []

                result[row[category_field]].append(row)

            # save data
            for cat in result.keys():
                filename = self.get_file_name('', cat)
                filename_dir = self._get_save_dir(os.path.dirname(filename))

                if not os.path.exists(filename_dir):
                    DataSaver.fix_dirs(filename_dir)

                self._save(result[cat], data_fields, self.get_file_name('', cat), {})

    @abstractmethod
    def _save(self, data: [], data_fields: [], out_file: str, params: {}) -> None:
        pass

    # TODO: rework?
    def _get_save_dir(self, filename):
        return os.path.join(get_script_directory(), '../..', self.output_dir, filename)

    def _check_data(self) -> bool:
        if not self.data:
            logger.warning('Empty data source')
            return False

        return True

    # noinspection PyMethodMayBeStatic
    def _check_data_fields(self, data: [], data_fields: []) -> []:
        if len(data) > 0:
            # check valid field records or not - take data[0] because all items have same fields
            data_fields_checked = [f for f in data_fields if f in data[0]]

            if len(data_fields) != len(data_fields_checked):
                logger.warning(f'Undefined properties removed! \n'
                               f'\tOld: {data_fields}\n'
                               f'\tvs\n'
                               f'\tNew: {data_fields_checked}')

            return data_fields_checked

    @staticmethod
    def fix_row_encoding(row: {}, encoding: str, mode: str='replace'):
        for field in row.keys():
            row[field] = row[field].encode(encoding, mode).decode(encoding)

    @staticmethod
    def fix_dirs(base_dir, *add_dirs: str):
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        for add_dir in add_dirs:
            new_dir = os.path.join(base_dir, add_dir)
            if not os.path.exists(new_dir):
                os.makedirs(new_dir)
