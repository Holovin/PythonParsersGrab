# r1

import json
import logging
import os


from helpers.save.data_saver import DataSaver

logger = logging.getLogger('ddd_site_parse')


class DataSaverJSON(DataSaver):
    def __init__(self, params: {}):
        super().__init__(params)

        self.ext = 'json'
        self.newline = params.get('newline', '')

    def _save(self, data: [], data_fields: [], out_file: str, params: {}) -> None:
        output_path = os.path.join(self.output_dir, out_file)

        with open(output_path, 'w', newline=self.newline, encoding=self.encoding) as output:
            self._check_data_fields(data, data_fields)
            output.write('[\n')

            for row in data:
                try:
                    output.write(f'{json.dumps(dict((key, value) for key, value in row.items() if key in data_fields), indent=1, ensure_ascii=False)},\n')

                except UnicodeEncodeError as e:
                    logging.debug(f'[E: {e}] Write row error, trying fix encoding: [{row}]')
                    DataSaver.fix_row_encoding(row, self.encoding)

                    output.write(f'{json.dumps(dict((key, value) for key, value in row.items() if key in data_fields), indent=1, ensure_ascii=False)},\n')

            # remove last \n and comma, cause it occur invalid json
            output.seek(output.tell() - 2, 0)
            output.write('\n]')
