import re

from d_parser.d_spider_common import DSpiderCommon
from d_parser.helpers.re_set import Ree
from helpers.url_generator import UrlGenerator
from d_parser.helpers.stat_counter import StatCounter as SC


VERSION = 29


# Warn: Don't remove task argument even if not use it (it's break grab and spider crashed)
# Warn: noinspection PyUnusedLocal
class DSpider(DSpiderCommon):
    re_product_status = re.compile('^.*?((\d+-)?(?P<int>\d+)).+')

    def __init__(self, thread_number, try_limit=0):
        super().__init__(thread_number, try_limit)

    # parse categories
    def task_initial(self, grab, task):
        try:
            if self.check_body_errors(grab, task):
                yield self.check_errors(task)
                return

            links = grab.doc.select('//nav//a[not(.//img) and re:match(@href, "/product_list/.+")]')

            for link in links:
                url = UrlGenerator.get_page_params(self.domain, link.attr('href'), {'count': 999999, 'name': 'asc'})
                yield self.do_task('parse_page', url, DSpider.get_next_task_priority(task))

        except Exception as e:
            self.process_error(grab, task, e)

        finally:
            self.process_finally(task)

    # parse page
    def task_parse_page(self, grab, task):
        try:
            if self.check_body_errors(grab, task):
                yield self.check_errors(task)
                return

            # parse items links                         # yep, with u letter
            items_links = grab.doc.select('//div[@class="pruduct_grid"]//a[@class="pruduct_grid_title"]')

            for index, row in enumerate(items_links):
                link = row.attr('href')

                # make absolute urls if needed
                if link[:1] == '/':
                    link = UrlGenerator.get_page_params(self.domain, link, {})

                yield self.do_task('parse_item', link, DSpider.get_next_task_priority(task))

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
            product_info = grab.doc.select('//div[@class="item_good"]')

            # parse fields
            # A = name
            product_name = product_info.select('.//h1').text()

            # B = [const]
            product_count_string = product_info.select('.//div[@class="availability"]').text()
            product_count = '-1'

            # E = price
            # if E = "запросить цену и наличие" => -1
            # else => float
            product_price_raw = product_info.select('.//div[@class="cupit"]')

            if 'запросить' in product_price_raw.text() and product_count_string == 'В наличии':
                # C = status
                # if B = "в наличии" => 0
                product_status = '0'
                product_price = '-1'

            else:
                # E = price (float)
                product_price = product_info.select('.//div[@class="cupit"]/div[1]/span/following-sibling::text()[1]').text(default='[not found]')

                # check if correct price
                if not Ree.float.match(product_price):
                    self.log_warn(SC.MSG_UNKNOWN_PRICE, f'Skip item, cuz wrong price {product_price}', task)
                    return

                # C = status
                # if B = "в наличии" => 000000000
                # if B = "Под заказ [DIGIT1]-[DIGIT2] дня" => [DIGIT2]
                # if B = "Под заказ [DIGIT2]          дня" => [DIGIT2]
                if product_count_string == 'В наличии':
                    product_status = '0'

                else:
                    product_status_raw = self.re_product_status.match(product_count_string)

                    if product_status_raw:
                        product_status_raw = self.re_product_status.match(product_count_string).groupdict()['int']

                        if Ree.number.match(product_status_raw):
                            product_status = product_status_raw

                            if int(product_status) > 20:
                                self.log_warn(SC.MSG_UNKNOWN_PRICE, f'Skip because {product_status} is more 20', task)
                                return

                        else:
                            self.log_warn(SC.MSG_UNKNOWN_PRICE, f'Skip because {product_count_string} is unknown status (1)', task)
                            return

                    else:
                        self.log_warn(SC.MSG_UNKNOWN_PRICE, f'Skip because {product_count_string} is unknown status (2)', task)
                        return

            # D = unit
            product_unit = product_info.select('.//div[@class="unit"]').text()

            if product_unit == '':
                product_unit = 'ед.'

            # F = vendor code
            product_vendor_code = product_info.select('.//p/span[1]/span[1]').text()

            # G = vendor
            product_vendor = product_info.select('.//p/span[2]/span[1]').text()

            # H = photo url
            product_photo_url_raw = product_info.select('./div[@class="photo"]//img').attr('src')
            product_photo_url = UrlGenerator.get_page_params(self.domain, product_photo_url_raw, {})

            # I = description
            product_description_raw = grab.doc.select('//div[@class="tabs"]/div/div')

            product_description = {'Описание': product_description_raw.select('./div[2]/p').text()}

            table = product_description_raw.select('./div[1]//tr')

            for row in table:
                key = row.select('./td[1]').text().strip(':')
                value = row.select('./td[2]').text()

                if key:
                    product_description[key] = value

            # ID
            product_id = Ree.extract_int.match(product_info.select('.//div[@class="basket add_basket"]/a').attr('id', ''))

            if product_id:
                product_id = product_id.groupdict()['int']
            else:
                product_id = ''

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
                'id': product_id,
                'properties': product_description
            })

        except Exception as e:
            self.process_error(grab, task, e)

        finally:
            self.process_finally(task)
