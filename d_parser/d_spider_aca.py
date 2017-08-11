import logging

from grab.spider import Spider, Task

from d_parser.helpers.cookies_init import cookies_init
from d_parser.helpers.el_parser import get_max_page
from d_parser.helpers.parser_extender import check_body_errors, process_error, common_init
from d_parser.helpers.re_set import Ree
from helpers.config import Config
from helpers.url_generator import UrlGenerator


# Warn: Don't remove task argument even if not use it (it's break grab and spider crashed)
# Warn: noinspection PyUnusedLocal
class DSpider(Spider):
    initial_urls = Config.get_seq('SITE_URL')

    def __init__(self, thread_number, writer, try_limit=0):
        super().__init__(thread_number=thread_number, network_try_limit=try_limit, priority_mode='const')
        DSpider._check_body_errors = check_body_errors
        DSpider._process_error = process_error
        DSpider._common_init = common_init
        self._common_init(writer, try_limit)

        Ree.init()
        Ree.is_page_number(Config.get('SITE_PAGE_PARAM'))

    def create_grab_instance(self, **kwargs):
        g = super(DSpider, self).create_grab_instance(**kwargs)
        return cookies_init(self.cookie_jar, g)

    def task_initial(self, grab, task):
        self.logger.debug('[{}] Initial url: {}'.format(task.name, task.url))

        if self._check_body_errors(grab, task):
            self.logger.fatal('[start] Err task with url {}, attempt {}'.format(task.url, task.task_try_count))
            return

        try:
            items = grab.doc.select('//div[@class="catalog-pagenav"]//a[contains(@href, "{}")]'.format(Config.get('SITE_PAGE_PARAM')))
            max_page = get_max_page(items)

            self.logger.info('[{}] Task: {}, max_page: {}'.format(task.name, task.url, max_page))

            url_gen = UrlGenerator(task.url, Config.get('SITE_PAGE_PARAM'))

            for p in range(1, max_page + 1):
                url = url_gen.get_page(p)
                yield Task('parse_page', url=url, priority=90)

        except Exception as e:
            self._process_error(grab, task, e)

        self.logger.info('[{}] Tasks added...'.format(task.name))

    def task_parse_page(self, grab, task):
        self.logger.debug('[{}] Parse page: {}'.format(task.name, task.url))

        try:
            if self._check_body_errors(grab, task):
                if task.task_try_count < self.err_limit:
                    self.logger.error('[{}] Restart task with url {}, attempt {}'.format(task.name, task.url, task.task_try_count))
                    yield Task('parse_items', url=task.url, priority=110, task_try_count=task.task_try_count + 1, raw=True)
                else:
                    self.logger.error('[{}] Skip task with url {}, attempt {}'.format(task.name, task.url, task.task_try_count))
                return

            table = grab.doc.select('//div[@class="catalog-section-it-table"]')

            # UNIT (global for all page)
            unit = table.select('.//div[@class="catalog_quantity"]').text().split(', ')[1].strip()

            rows = table.select('.//div[contains(@class, "catalog-section-it-row")]')

            for index, row in enumerate(rows):
                # COUNT
                count = row.select('./div[contains(@class, "catalog_quantity")]').text().strip()
                # skip if count is wrong
                if count == 'Ожидаетсяпоставка':
                    self.logger.debug('[{}] Text {} is not a number, skip (url: {})'.format(task.name, count, task.url))
                    continue
                # skip if count is wrong with err
                if not Ree.float.match(count):
                    self.logger.warning('[{}] Text {} is not a number, skip (url: {})'.format(task.name, count, task.url))
                    continue

                count = count.replace(',', '.')

                # PRICE
                price = Config.get('APP_PRICE_ON_REQUEST')

                # NAME
                item_name = row.select('./div[@class="name"]').text().strip()

                # Debug: go for all inner pages and try find price
                # link = row.select('./div[@class="name"]/a').attr('href')
                # yield Task('parse_items', url=urllib.parse.urljoin(self.domain, link), priority=100, raw=True)

                # OUTPUT
                self.logger.debug('[{}] Item added, index {} at url {}'.format(task.name, index, task.url))
                self.result.writerow([item_name, count, unit, price])

        except Exception as e:
            self._process_error(grab, task, e)

    # def task_parse_items(self, grab, task):
    #     if 'Узнать цену' not in get_body(grab):
    #         print(task.url)
