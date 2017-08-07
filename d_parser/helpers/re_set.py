import re

from helpers.config import Config


class Ree:
    number = None
    page_number = None
    price_extractor = None

    @staticmethod
    def is_page_number(page_param):
        # {PARAM}=1, like p=1
        #page_number = re.compile('{}=(?P<page>\d+)'.format(Config.get('SITE_PAGE_PARAM')))
        Ree.page_number = re.compile('{}=(?P<page>\d+)'.format(page_param))

    @staticmethod
    # DEPRECATED
    # DEPRECATED
    # DEPRECATED
    # DEPRECATED
    def price():
        # price.price, like [10.10]
        # WARN: dot without backslash, possible errors, but its already used
        price = re.compile('^\d+(.\d+)?$')

    @staticmethod
    def is_price_ext(price_sep):
        # price{SEP}price, like 10.10 or 11,11
        # price_extractor = re.compile('(?P<price>\d+(\{}\d+)?)'.format(Config.get('APP_PRICE_SEP')))
        Ree.price_extractor = re.compile('(?P<price>\d+(\{}\d+)?)'.format(price_sep))

    @staticmethod
    def is_number():
        Ree.number = re.compile('^\d+$')
