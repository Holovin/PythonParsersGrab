import csv
import logging
import os

import time

from config.config import Config
from d_spider import DSpider
from dev.logger import logger_setup


def main():
    # setup
    logger_setup(Config.get('APP_LOG_FILE'), ['ddd_site_parse'])

    # log
    logger = logging.getLogger('ddd_site_parse')
    logger.addHandler(logging.NullHandler())
    logger.info(' --- ')
    logger.info('Start app...')

    # bot
    output_file_name = time.strftime('%d_%m_%Y') + '.csv'
    output_path = os.path.join(Config.get('APP_OUTPUT_DIR'), output_file_name)

    if not os.path.exists(Config.get('APP_OUTPUT_DIR')):
        logger.info('Create directory, because not exist')
        os.makedirs(Config.get('APP_OUTPUT_DIR'))

    with open(output_path, 'w', newline='', encoding=Config.get('APP_OUTPUT_ENC')) as output:
        writer = csv.writer(output, delimiter=';')

        try:
            threads_counter = int(Config.get('APP_THREAD_COUNT'))
            bot = DSpider(thread_number=threads_counter, logger_name='ddd_site_parse', writer=writer)
            bot.run()

        except Exception as e:
            print(e)

    logger.info('End app...\n\n')


if __name__ == '__main__':
    main()
