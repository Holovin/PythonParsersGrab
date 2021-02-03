from d_parser.d_spider_common import DSpiderCommon
from d_parser.helpers.re_set import Ree
from d_parser.helpers.stat_counter import StatCounter as SC
from helpers.url_generator import UrlGenerator


VERSION = 291


# Warn: Don't remove task argument even if not use it (it's break grab and spider crashed)
# Warn: noinspection PyUnusedLocal
class DSpider(DSpiderCommon):
    def __init__(self, thread_number, try_limit=0):
        super().__init__(thread_number, try_limit)

    # fetch categories
    def task_initial(self, grab, task):
        try:
            if self.check_body_errors(grab, task):
                yield self.check_errors(task)
                return

            for link in self.links_todo:
                yield self.do_task('parse_page', link, DSpider.get_next_task_priority(task))

        except Exception as e:
            self.process_error(grab, task, e)

        finally:
            self.process_finally(task)

    def task_parse_page(self, grab, task):
        try:
            if self.check_body_errors(grab, task):
                yield self.check_errors(task)
                return

            if grab.doc.select('//title').text('') == 'Login - OTRS::ITSM 6':
                self.log.error('NO LOGIN')
                return

            title = grab.doc.select('//h1').text('')

            self.result.add({
                'title': title,
            })

        except Exception as e:
            self.process_error(grab, task, e)

        finally:
            self.process_finally(task)
