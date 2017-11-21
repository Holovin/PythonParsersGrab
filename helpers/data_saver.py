# data_saver.py
# Module for save data as single CSV or separated as some CSV files
# r2
# TODO: rework save method for support dynamic columns

import csv
import logging
import time
import os


logger = logging.getLogger('ddd_site_parse')


class DataSaver:
    def __init__(self, output_dir, log_dir, encoding):
        self.data = []
        self.output_dir = output_dir
        self.log_dir = log_dir
        self.encoding = encoding

    def set_data(self, data):
        self.data = data

    # save methods
    def save(self, newline='', delimiter=';'):
        output_file_name = '{}.{}'.format(time.strftime('%d_%m_%Y'), 'csv')
        logging.info('Saving single to file {}'.format(output_file_name))
        self._save(self.data, output_file_name, self.output_dir, self.encoding, newline, delimiter)

    def save_by_category(self, field, newline='', delimiter=';'):
        result = {}

        # sep data
        for row in self.data:
            # create cat array
            if row[field] not in result.keys():
                result[row[field]] = []

            result[row[field]].append(row)

        # save data
        for cat in result.keys():
            output_file_name = '{}_{}.{}'.format(time.strftime('%d_%m_%Y'), cat, 'csv')
            logging.info('Saving cats to file {}'.format(output_file_name))
            self._save(result[cat], output_file_name, self.output_dir, self.encoding, newline, delimiter)

    def fix_dirs(self):
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        log_dir = os.path.join(self.output_dir, self.log_dir)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

    # private
    @staticmethod
    def _save(data, out_file, out_dir, encoding, newline='', delimiter=';'):
        output_path = os.path.join(out_dir, out_file)

        with open(output_path, 'w', newline=newline, encoding=encoding) as output:
            writer = csv.writer(output, delimiter=delimiter)

            for row in data:
                try:
                    # Maybe bring out key names?
                    writer.writerow([row['name'], row['count'], row['unit'], row['price']])
                except UnicodeEncodeError as e:
                    logging.debug('[E: {}] Write row error, trying fix encoding: [{}]'.format(e, row))
                    DataSaver.fix_row_encoding(row, encoding)
                    writer.writerow([row['name'], row['count'], row['unit'], row['price']])

    @staticmethod
    def fix_row_encoding(row, encoding, mode='replace'):
        for field in row.keys():
            row[field] = row[field].encode(encoding, mode).decode(encoding)
