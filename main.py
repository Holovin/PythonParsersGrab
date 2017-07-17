import csv
import logging

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
    with open(Config.get('APP_OUTPUT_CSV'), 'w', newline='') as output:
        writer = csv.writer(output)

        try:
            threads_counter = int(Config.get('APP_THREAD_COUNT'))
            bot = DSpider(thread_number=threads_counter, logger_name='ddd_site_parse', writer=writer)
            bot.run()

        except Exception as e:
            print(e)

    logger.info('End app...\n\n')


if __name__ == '__main__':
    main()
