import logging
import re

from grab.spider import Spider, Task
from weblib.error import DataNotFound

from config.config import Config
from helpers.url_generator import UrlGenerator


# Don't remove task argument even if not use it (it's break grab and spider crashed)
# noinspection PyUnusedLocal
class DSpider(Spider):
    initial_urls = [Config.get('SITE_URL')]

    def __init__(self, thread_number, logger_name, writer):
        super().__init__(thread_number)
        self.logger = logging.getLogger(logger_name)
        self.result = writer

    def task_initial(self, grab, task):
        re_page_number = re.compile('{}=(\d+)'.format(Config.get('SITE_PAGE_PARAM')))
        max_page = 0

        for page_link in grab.doc.select('//a[contains(@href, "{}")]'.format(Config.get('SITE_PAGE_PARAM'))):
            match = re_page_number.search(page_link.attr('href'))

            if len(match.groups()) == 1:
                page_number = match.group(1)
                self.logger.debug('Find max_page: {}'.format(page_number))

                int_page_number = int(page_number)

                if int_page_number > max_page:
                    self.logger.debug('Set new max_page: {} => {}'.format(max_page, page_number))
                    max_page = int_page_number

        else:
            self.logger.debug('Max page is: {}'.format(max_page))

            if max_page < 1:
                err = 'Bad page counter: {}'.format(max_page)
                self.logger.error(err)
                raise Exception(err)

        url_gen = UrlGenerator(Config.get('SITE_URL'), Config.get('SITE_PAGE_PARAM'))

        for p in range(1, max_page + 1):
            url = url_gen.get_page(p)
            yield Task('parse_page', url=url)

        self.logger.info('Tasks added...')

    def task_parse_page(self, grab, task):
        self.logger.info('Start task: {}'.format(task.url))

        rows = grab.doc.select('//div[@class="content"]/table[@class="item_list"]//tr')
        self.logger.debug('Index / Pic_Url / Name / Count / d / D / B / Price')

        for index, row in enumerate(rows):
            try:
                item_name = row.select('./td[@class="item_name"]').text()
                pic = row.select('./td[@class="pic"]//img').attr('src')
                count = row.select('./td[@class="item_quant"]').text()
                inner_d = row.select('./td[@class="innerd"]').text()
                outer_d = row.select('./td[@class="outerd"]').text()
                width = row.select('./td[@class="width"]').text()
                price = row.select('./td[@class="price"]').text()

            except DataNotFound:
                self.logger.debug('Skip line {}'.format(index))
                continue

            self.result.writerow([item_name, pic, count, inner_d, outer_d, width, price])
            self.logger.debug('Index: {} | {} {} {} {} {} {}'
                              .format(index, item_name, pic, count, inner_d, outer_d, width, price))

        self.logger.info('Task {} end'.format(task.url))
