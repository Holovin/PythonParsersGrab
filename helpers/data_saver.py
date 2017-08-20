import csv
import logging
import time
import os


logger = logging.getLogger('ddd_site_parse')


class DataSaver:
    def __init__(self, data, output_dir, encoding):
        self.data = data
        self.output_dir = output_dir
        self.encoding = encoding

    # helpers
    def fix_field_encoding(self, field, encoding, mode='replace'):
        if not encoding:
            encoding = self.encoding

        for index, row in enumerate(self.data):
            row[index][field] = row[index][field].encode(encoding, mode).decode(encoding)

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

    # private
    @staticmethod
    def _save(data, out_file, out_dir, encoding, newline='', delimiter=';'):
        output_path = os.path.join(out_dir, out_file)

        with open(output_path, 'w', newline=newline, encoding=encoding) as output:
            writer = csv.writer(output, delimiter=delimiter)

            for row in data:
                # Maybe bring out key names?
                writer.writerow([row['name'], row['count'], row['unit'], row['price']])
