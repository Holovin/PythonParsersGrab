import re

from helpers.config import Config


class Ree:
    page_number = re.compile('{}=(?P<page>\d+)'.format(Config.get('SITE_PAGE_PARAM')))
    price = re.compile('^\d+(.\d+)?$')
    number = re.compile('^\d+$')
