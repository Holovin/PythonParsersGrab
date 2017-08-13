import csv
import importlib
import logging
import operator
import os
import time
import sys

from functools import reduce
from datetime import datetime

from dev.logger import logger_setup
from helpers.config import Config
from helpers.module_loader import ModuleLoader


def init_loggers():
    logger_setup(
        os.path.join(Config.get('APP_OUTPUT_DIR'), Config.get('APP_LOG_DIR'), Config.get('APP_LOG_DEBUG_FILE')),
        ['ddd_site_parse'], True)

    logger_setup(
        os.path.join(Config.get('APP_OUTPUT_DIR'), Config.get('APP_LOG_DIR'), Config.get('APP_LOG_GRAB_FILE')), [
            'grab.document',
            'grab.spider.base',
            'grab.spider.task',
            'grab.spider.base.verbose'
            'grab.proxylist',
            'grab.stat',
            'grab.script.crawl'
        ]
    )

    logger = logging.getLogger('ddd_site_parse')
    logger.addHandler(logging.NullHandler())

    return logger


def process_stats(stats):
    output = ''

    if not stats:
        return output

    _stats = sorted(stats.items(), key=operator.itemgetter(1), reverse=True)
    _max = reduce(lambda a, b: a+b, stats.values())

    for row in _stats:
        output += 'Code: {}, count: {}% ({} / {})\n'.format(row[0], row[1]/_max * 100, row[1], _max)

    return output


def fix_dirs():
    if not os.path.exists(Config.get('APP_OUTPUT_DIR')):
        os.makedirs(Config.get('APP_OUTPUT_DIR'))

    log_dir = os.path.join(Config.get('APP_OUTPUT_DIR'), Config.get('APP_LOG_DIR'))
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)


def load_config():
    if len(sys.argv) > 1:
        Config.load(os.path.join(os.path.dirname(__file__), 'config'), sys.argv[1])
        return True

    return False


def main():
    # load config
    if not load_config():
        exit(2)

    # output dirs
    fix_dirs()

    # log
    logger = init_loggers()
    logger.info(' --- ')
    logger.info('Start app...')

    # output
    output_file_name = time.strftime('%d_%m_%Y') + '.csv'
    output_path = os.path.join(Config.get('APP_OUTPUT_DIR'), output_file_name)

    # loader
    loader = ModuleLoader('d_parser.{}'.format(Config.get('APP_PARSER')))
    d_spider = loader.get('DSpider')

    # post-work
    need_post = Config.get('APP_NEED_POST', '')
    if need_post == 'True':
        d_post_work = loader.get('do_post_work')
    else:
        d_post_work = None

    # bot
    with open(output_path, 'w', newline='', encoding=Config.get('APP_OUTPUT_ENC')) as output:
        writer = csv.writer(output, delimiter=';')

        try:
            logger.info('{} :: Start...'.format(datetime.now().strftime('%Y/%m/%d %H:%M:%S')))
            threads_counter = int(Config.get('APP_THREAD_COUNT'))
            bot = d_spider(thread_number=threads_counter, writer=writer, try_limit=int(Config.get('APP_TRY_LIMIT')))
            bot.run()

            if need_post and d_post_work:
                d_post_work()

            logger.info('End with stats: \n{}'.format(process_stats(bot.status_counter)))

        except Exception as e:
            err = 'App core fatal error: {}'.format(e)

            logger.fatal(err)

    logger.info('{} :: End...'.format(datetime.now().strftime('%Y/%m/%d %H:%M:%S')))


if __name__ == '__main__':
    main()
