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
        self.csv_newline = params.get('csv_newline', '')
        self.csv_delimiter = params.get('csv_delimiter', ';')

    def save(self, data_fields: [], params: {}) -> None:
        self._save(self.data, data_fields, self.get_file_name(''))

    def save_by_category(self, data_fields: [], category_field: str, params: {}) -> None:
        result = {}

        # sep data
        for row in self.data:
            # create cat array
            if row[category_field] not in result.keys():
                result[row[category_field]] = []

            result[row[category_field]].append(row)

        # save data
        for cat in result.keys():
            self._save(result[cat], data_fields, self.get_file_name('', cat))

    # private
    def _save(self, data: [], data_fields: [], out_file: str) -> None:
        output_path = os.path.join(self.output_dir, out_file)

        with open(output_path, 'w', newline=self.csv_newline, encoding=self.encoding) as output:
            writer = csv.writer(output, delimiter=self.csv_delimiter)

            if len(data) > 0:
                # check valid field records or not - take data[0] because all items have same fields
                data_fields_checked = [f for f in data_fields if f in data[0]]

                if len(data_fields) != len(data_fields_checked):
                    logger.warning('Undefined properties removed! \nOld: {} \nvs\nNew: {}'.format(data_fields, data_fields_checked))

            else:
                logger.fatal('Empty data source')
                raise Exception('Empty data source')

            for row in data:
                try:
                    writer.writerow([row[field] for field in data_fields])

                except UnicodeEncodeError as e:
                    logging.debug('[E: {}] Write row error, trying fix encoding: [{}]'.format(e, row))
                    DataSaver.fix_row_encoding(row, self.encoding)

                    writer.writerow([row[field] for field in data_fields])
