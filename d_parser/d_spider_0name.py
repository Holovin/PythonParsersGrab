from d_parser.d_spider_common import DSpiderCommon
from helpers.config import Config


VERSION = 29


# Warn: Don't remove task argument even if not use it (it's break grab and spider crashed)
# Warn: noinspection PyUnusedLocal
class DSpider(DSpiderCommon):
    def __init__(self, thread_number, try_limit=0):
        super().__init__(thread_number, try_limit)
        self.limit = int(Config.get('LIMIT'))

    def task_generator(self):
        for _ in range(0, self.limit):
            yield self.do_task('parse', self.domain, 90, last=True)

    def task_parse(self, grab, task):
        try:
            if self.check_body_errors(grab, task):
                yield self.check_errors(task)
                return

            name = grab.doc.select('//h2[2]').text('')

            # save
            if name:
                self.log.info(f'Add site: {name}', task)
                self.result.add({'name': name})

        except Exception as e:
            self.process_error(grab, task, e)

        finally:
            self.process_finally(task, last=True)
