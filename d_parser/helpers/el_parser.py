# el_parser.py
# Common parser functions
# r1

import logging

from d_parser.helpers.re_set import Ree

logger = logging.getLogger('ddd_site_parse')


# legacy version (<2.4.1)
def get_max_page(items, max_page=1, err_page=0):
    return _parse_pagination(items, max_page, err_page)[0]


# new version (>=2.4.1)
def get_pagination(links, max_page=1, min_page_for_err=0):
    return _parse_pagination(links, max_page, min_page_for_err)


# common version
def _parse_pagination(items, max_page, min_page_for_err):
    page_param = None

    for page_link in items:
        match = Ree.page_number.search(page_link.attr('href'))

        if match:
            page_number = match.groupdict()['page']
            page_param = match.groupdict()['param']
            logger.debug('[get_max_page] Find max_page: {}'.format(page_number))

            int_page_number = int(page_number)

            if int_page_number > max_page:
                logger.debug('[get_max_page] Set new max_page: {} => {}'.format(max_page, page_number))
                max_page = int_page_number

    else:
        if max_page <= min_page_for_err:
            raise Exception('Bad page number')

        logger.debug('[get_max_page] Max page is: {}'.format(max_page))

    if not page_param:
        logger.error('[get_max_page] Cant parse page param')
        raise Exception('Cant parse page param')

    return max_page, page_param

