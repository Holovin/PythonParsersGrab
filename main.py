import csv
import logging
import os
import time

from dev.logger import logger_setup
from helpers.config import Config
from helpers.output import Output
from parser.d_spider import DSpider


def init_loggers():
    logger_setup(Config.get('APP_LOG_DEBUG_FILE'), [
        'ddd_site_parse',
    ], True)

    logger_setup(Config.get('APP_LOG_GRUB_FILE'), [
        'grab.document',
        'grab.spider.base',
        'grab.spider.task',
        'grab.spider.base.verbose'
        'grab.proxylist',
        'grab.stat',
        'grab.script.crawl'
    ])

    logger = logging.getLogger('ddd_site_parse')
    logger.addHandler(logging.NullHandler())

    return logger


def main():
    # output config
    Output(True if Config.get('APP_CAN_OUTPUT') == 'True' else False)

    # log
    logger = init_loggers()
    logger.info(' --- ')
    logger.info('Start app...')

    # output
    output_file_name = time.strftime('%d_%m_%Y') + '.csv'
    output_path = os.path.join(Config.get('APP_OUTPUT_DIR'), output_file_name)

    if not os.path.exists(Config.get('APP_OUTPUT_DIR')):
        logger.info('Create directory, because not exist')
        os.makedirs(Config.get('APP_OUTPUT_DIR'))

    # bot
    with open(output_path, 'w', newline='', encoding=Config.get('APP_OUTPUT_ENC')) as output:
        writer = csv.writer(output, delimiter=';')

        try:
            threads_counter = int(Config.get('APP_THREAD_COUNT'))
            bot = DSpider(
                thread_number=threads_counter,
                logger_name='ddd_site_parse',
                writer=writer,
                try_limit=int(Config.get('APP_TRY_LIMIT'))
            )
            bot.run()

        except Exception as e:
            Output.print(e)

    logger.info('End app...\n\n')


if __name__ == '__main__':
    main()
