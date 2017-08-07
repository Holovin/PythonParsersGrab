import logging

from d_parser.helpers.re_set import Ree

logger = logging.getLogger('ddd_site_parse')


def get_max_page(items, max_page=1, err_page=0):
    for page_link in items:
        match = Ree.page_number.search(page_link.attr('href'))

        if match:
            page_number = match.groupdict()['page']
            logger.debug('[prep] Find max_page: {}'.format(page_number))

            int_page_number = int(page_number)

            if int_page_number > max_page:
                logger.debug('[prep] Set new max_page: {} => {}'.format(max_page, page_number))
                max_page = int_page_number

    else:
        if max_page <= err_page:
            raise Exception('Bad page number')

        logger.debug('[prep] Max page is: {}'.format(max_page))

    return max_page
