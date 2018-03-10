from d_parser.d_spider_common import DSpiderCommon
from d_parser.helpers.re_set import Ree
from helpers.url_generator import UrlGenerator
from d_parser.helpers.stat_counter import StatCounter as SC


VERSION = 29


# Warn: Don't remove task argument even if not use it (it's break grab and spider crashed)
# Warn: noinspection PyUnusedLocal
class DSpider(DSpiderCommon):
    def __init__(self, thread_number, try_limit=0):
        super().__init__(thread_number, try_limit)

    # fetch items
    def task_initial(self, grab, task):
        try:
            if self.check_body_errors(grab, task):
                yield self.check_errors(task)
                return

            items_list = grab.doc.select('//div[@class="b-megamenu-cats"]//a[@class="b-megamenu-cats__title"]')

            for link in items_list:
                # DONT USE PAGE_SIZE PARAMS >>> CAUSE A LOT OF 404 ERRORS
                link = UrlGenerator.get_page_params(self.domain, link.attr('href'), {})
                yield self.do_task('parse_page', link,  DSpider.get_next_task_priority(task))

        except Exception as e:
            self.process_error(grab, task, e)

        finally:
            self.process_finally(task)

    # parse page items
    def task_parse_page(self, grab, task):
        try:
            if self.check_body_errors(grab, task):
                yield self.check_errors(task)
                return

            # parse items links
            items_list = grab.doc.select('//div[contains(@class, "b-items-item")]//a[@itemprop="name"]')

            for link in items_list:
                link = UrlGenerator.get_page_params(self.domain, link.attr('href'), {})
                yield self.do_task('parse_item', link, DSpider.get_next_task_priority(task))

            # parse next page link
            next_page = grab.doc('//div[@class="b-paging"][1]/a[@class="b-paging__right" and text()="Следующая"]').attr('href', '')

            if next_page:
                next_page = UrlGenerator.get_page_params(self.domain, next_page, {})
                yield self.do_task('parse_page', next_page, DSpider.get_next_task_priority(task, 0))

        except Exception as e:
            self.process_error(grab, task, e)

        finally:
            self.process_finally(task)

    # parse single item
    def task_parse_item(self, grab, task):
        try:
            if self.check_body_errors(grab, task):
                yield self.check_errors(task)
                return

            # common block with info
            product_info = grab.doc.select('//div[@itemtype="http://schema.org/Product"]')

            # parse fields
            # A = name
            product_name = product_info.select('.//h1').text()

            # Table D, F, G:
            table_info = product_info.select('.//div[@class="good-info-left-part good-left-low-properties"]/div[@class="row"]')

            product_vendor = ''
            product_vendor_code = ''
            product_unit = 'ед.'

            for row in table_info:
                line = row.text('')

                if line:
                    # D = unit (measure)
                    if 'Единица измерения' in line:
                        product_unit = line.replace('Единица измерения: ', '').replace(' ', '')

                    # G = vendor (manufacture)
                    elif 'Производитель' in line:
                        product_vendor = line.replace('Производитель: ', '').replace(' ', '')

                    # F = vendor code (sku)
                    elif 'Артикул' in line:
                        product_vendor_code = line.replace('Артикул: ', '').replace(' ', '')

            # E = price || .//div[@itemprop="price"]/span
            product_price = product_info.select('.//div[@class="good-info-price"]').text('').replace(' руб.', '')

            if product_price == 'Цена по запросу':
                product_price = '-1'

            elif not product_price or not Ree.float.match(product_price):
                self.log_warn(SC.MSG_UNKNOWN_PRICE, f'Unknown price status {product_price}, skip...', task)
                return

            # H = photo url
            product_photo_url_raw = grab.doc.select('//div[@class="b-good-images"]//img[@itemprop="logo"]').attr('src', '')

            if product_photo_url_raw:
                product_photo_url = UrlGenerator.get_page_params(self.domain, product_photo_url_raw, {})
            else:
                product_photo_url = ''

            # Description tabs
            desc_tabs = grab.doc.select('//div[contains(@class, "good-other-information")]')

            # I = description (properties)
            product_description = {
                'Описание': desc_tabs.select('.//div[@id="good-description"]').text('')
            }

            # I [part 2]
            table = desc_tabs.select('.//div[@id="good-properties"]/table//tr')

            for row in table:
                line = row.select('./td[@class="b-props__label"]').text('')
                value = row.select('./td[@class="b-props__value"]').text('')

                if line:
                    product_description[line] = value

            # B = count (quantity) [const -1]
            product_count = '-1'

            # store counters for save status check
            store_counter = {
                'Аква 100 (Одинцово)': 0,
                'Магазин на Ленинском': 0,
                'Магазин на Дмитровке': 0,
                'Центральный склад': 0,
                'Магазин в Питере': 0,
                'Магазин в Челябинске': 0
            }

            # C = status (delivery)
            count_in_stores_table = product_info.select('.//table[@class="b-sklad-table"]//tr')

            # parse stores from page
            for store in count_in_stores_table:
                line = store.select('./td[@class="b-sklad-table__name"]').text('')
                value = store.select('./td[2]').text('')

                if line == '':
                    self.log_warn(SC.MSG_UNKNOWN_STORE, f'Empty store!', task)
                    continue

                # check store in list
                if line not in store_counter:
                    self.log_warn(SC.MSG_UNKNOWN_STORE, f'Store "{line}" not found in list!', task)
                    continue

                # mark store as processed
                store_counter[line] += 1

                # check status
                if 'В наличии' == value:
                    product_status = '0'

                else:
                    product_status = '-1'

                # set place for future sort
                product_place = line

                # save
                self.result.add({
                    'name': product_name,
                    'quantity': product_count,
                    'delivery': product_status,
                    'measure': product_unit,
                    'price': product_price,
                    'sku': product_vendor_code,
                    'manufacture': product_vendor,
                    'photo': product_photo_url,
                    'properties': product_description,
                    'place': product_place,
                })

            # check if miss some stores
            for store_name, store_times in store_counter.items():
                # skip if store used
                if store_times > 0:
                    continue

                # skip if price not -1 [not "on demand"]
                if product_price != '-1':
                    self.log_warn(SC.MSG_UNKNOWN_STATUS, f'Correct price "{product_price}" and missed store "{store_name}", WTF?!', task)
                    continue

                # save
                self.result.add({
                    'name': product_name,
                    'quantity': product_count,
                    'delivery': '-1',
                    'measure': product_unit,
                    'price': product_price,
                    'sku': product_vendor_code,
                    'manufacture': product_vendor,
                    'photo': product_photo_url,
                    'properties': product_description,
                    'place': store_name,
                })

        except Exception as e:
            self.process_error(grab, task, e)

        finally:
            self.process_finally(task)
