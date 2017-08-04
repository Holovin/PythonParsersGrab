import re

from helpers.config import Config


class Ree:
    # {PARAM}=1, like p=1
    page_number = re.compile('{}=(?P<page>\d+)'.format(Config.get('SITE_PAGE_PARAM')))

    # price.price, like [10.10]
    # WARN: dot without backslash, possible errors, but its already used
    price = re.compile('^\d+(.\d+)?$')

    # price{SEP}price, like 10.10 or 11,11
    price_extractor = re.compile('(?P<price>\d+(\{}\d+)?)'.format(Config.get('APP_PRICE_SEP')))

    # Just number check (maybe better check with python methods?)
    number = re.compile('^\d+$')
