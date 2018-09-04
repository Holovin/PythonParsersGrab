import operator

from d_parser.d_spider_common import DSpiderCommon
from helpers.url_generator import UrlGenerator


VERSION = 29


# Warn: Don't remove task argument even if not use it (it's break grab and spider crashed)
# Warn: noinspection PyUnusedLocal
class DSpider(DSpiderCommon):
    def __init__(self, thread_number, try_limit=0):
        super().__init__(thread_number, try_limit)

    # stub
    def task_initial(self, grab, task):
        try:
            if self.check_body_errors(grab, task):
                yield self.check_errors(task)
                return

            yield self.do_task('parse_page', task.url, DSpider.get_next_task_priority(task), skip_repeating=True, warn_repeating=False)

        except Exception as e:
            self.process_error(grab, task, e)

        finally:
            self.process_finally(task)

    # parse links
    def task_parse_page(self, grab, task):
        try:
            if self.check_body_errors(grab, task):
                yield self.check_errors(task, skip_repeating=True, warn_repeating=False)
                return

            # parse items links
            items_list = grab.doc.select('//a')

            for link in items_list:
                rel_url = link.attr('href', '')

                if not rel_url:
                    continue

                link = UrlGenerator.get_page_params(self.domain, link.attr('href'), {})

                yield self.do_task('parse_page', link, DSpider.get_next_task_priority(task), skip_repeating=True, warn_repeating=False)

        except Exception as e:
            self.process_error(grab, task, e)

        finally:
            self.process_finally(task)

    def d_post_work(self):
        for row in sorted(self.links.data.items(), key=lambda kv: kv[1], reverse=True):
            self.result.add({
                'uri': row[0],
                'rate': row[1]
            })
