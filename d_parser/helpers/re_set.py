# re_set.py
# Module for generating regex rules
# r1


import re


class Ree:
    float = None
    number = None
    page_number = None
    extract_int = None

    @staticmethod
    def init():
        Ree.is_float()
        Ree.is_number()
        Ree.is_page_number('')
        Ree.extract_int_compile()

    @staticmethod
    def is_page_number(page_param):
        Ree.page_number = re.compile('(?P<param>{})=(?P<page>\d+)'.format(page_param))

    @staticmethod
    def is_float(price_sep=',.'):
        Ree.float = re.compile('(?P<price>\d+([{}]\d+)?)'.format(price_sep))

    @staticmethod
    def is_number():
        Ree.number = re.compile('^\d+$')

    @staticmethod
    def extract_int_compile():
        Ree.extract_int = re.compile('^.*?(?P<int>\d+).+$')
