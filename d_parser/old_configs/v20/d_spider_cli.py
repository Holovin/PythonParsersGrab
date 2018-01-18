from grab.spider import Spider, Task

from d_parser.helpers.cookies_init import cookies_init
from d_parser.helpers.parser_extender import check_body_errors, process_error, common_init
from d_parser.helpers.re_set import Ree
from helpers.config import Config


# Warn: Don't remove task argument even if not use it (it's break grab and spider crashed)
# Warn: noinspection PyUnusedLocal
class DSpider(Spider):
    initial_urls = Config.get_seq('SITE_URL')

    def __init__(self, thread_number, try_limit=0):
        super().__init__(thread_number=thread_number, network_try_limit=try_limit, priority_mode='const')
        DSpider._check_body_errors = check_body_errors
        DSpider._process_error = process_error
        DSpider._common_init = common_init
        self._common_init(try_limit)

        Ree.init()
        Ree.is_page_number(Config.get('SITE_PAGE_PARAM'))

    def create_grab_instance(self, **kwargs):
        g = super(DSpider, self).create_grab_instance(**kwargs)
        return cookies_init(self.cookie_jar, g)

    def task_initial(self, grab, task):
        self.logger.debug('[{}] Initial url: {}'.format(task.name, task.url))

        if self._check_body_errors(grab, task):
            self.logger.fatal('[{}] Err task with url {}, attempt {}'.format(task.name, task.url, task.task_try_count))
            return

        try:
            table_wrapper = grab.doc.select('//div[contains(@class, "table-wrapper")]')

            # UNIT (global for all page)
            unit = table_wrapper.select('./table/thead//th[5]').text().split(', ')[1].strip()

            rows = table_wrapper.select('./table/tbody/tr[td]')

            for index, row in enumerate(rows):
                # COUNT
                # replace all spaces, because count can be like '1 111' when its = 1111
                count = row.select('./td[5]').text().replace(' ', '')

                # skip if count is wrong
                if not Ree.number.match(count):
                    # here skipped first 2 rows, its ok
                    self.logger.debug('[{}] Text {} is not a number, skip (url: {})'.format(task.name, count, task.url))
                    continue

                # PRICE
                price_raw = row.select('./td[6]').text().strip()
                match = Ree.float.match(price_raw)
                # check & fix
                if not match:
                    self.logger.warning('[{}] Skip item, because price is {} (line: {})'.format(task.name, price_raw, index))
                    continue

                price = match.groupdict()['price'].replace(',', '.')

                # NAME
                item_name = row.select('./td[2]').text().strip()

                if not item_name:
                    self.logger.debug('[{}] Text {} is not a name, skip (url: {})'.format(task.name, item_name, task.url))
                    continue

                # OUTPUT
                self.logger.debug('[{}] Item added, index {} at url {}'.format(task.name, index, task.url))
                self.result.append({
                   'name': item_name,
                   'count': count,
                   'unit': unit,
                   'price': price
                })

        except Exception as e:
            self._process_error(grab, task, e)
