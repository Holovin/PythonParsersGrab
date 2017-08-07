import logging

from d_parser.helpers.get_body import get_body
from helpers.output import Output

logger = logging.getLogger('ddd_site_parse')


def check_body_errors(self, grab, task):
    try:
        self.status_counter[str(grab.doc.code)] += 1

    except KeyError:
        self.status_counter[str(grab.doc.code)] = 1

    if grab.doc.body == '' or grab.doc.code != 200:
        err = '[{}] Code is {}, url is {}, body is {}'.format(task.name, grab.doc.code, task.url, grab.doc.body)
        Output.print(err)
        logger.error(err)
        return True

    return False


def process_error(self, grab, task, exception):
    try:
        self.status_counter['EXC'] += 1

    except KeyError:
        self.status_counter['EXC'] = 1

    html = get_body(grab)
    err = '[{}] Url {} parse failed (e: {}), debug: {}'.format(task.name, task.url, exception, html)
    Output.print(err)
    self.logger.error(err)
