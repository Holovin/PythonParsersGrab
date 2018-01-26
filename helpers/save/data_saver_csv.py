# r1

import csv
import logging
import os

from helpers.save.data_saver import DataSaver

logger = logging.getLogger('ddd_site_parse')


class DataSaverCSV(DataSaver):
    def __init__(self, params: {}):
        super().__init__(params)

        self.ext = 'csv'
        self.newline = params.get('newline', '')
        self.csv_delimiter = params.get('csv_delimiter', ';')

    def _save(self, data: [], data_fields: [], out_file: str, params: {}) -> None:
        output_path = os.path.join(self.output_dir, out_file)

        with open(output_path, 'w', newline=self.newline, encoding=self.encoding) as output:
            writer = csv.writer(output, delimiter=self.csv_delimiter)
            self._check_data_fields(data, data_fields)

            for row in data:
                try:
                    writer.writerow([row[field] for field in data_fields])

                except UnicodeEncodeError as e:
                    logging.debug(f'[E: {e}] Write row error, trying fix encoding: [{row}]')
                    DataSaver.fix_row_encoding(row, self.encoding)

                    writer.writerow([row[field] for field in data_fields])
