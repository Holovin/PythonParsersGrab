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
        Ree._is_float()
        Ree._is_number()
        Ree._is_page_number('')
        Ree._extract_int_compile()

    @staticmethod
    def _is_page_number(page_param):
        Ree.page_number = re.compile('(?P<param>{})=(?P<page>\d+)'.format(page_param))

    @staticmethod
    def _is_float(price_sep=',.'):
        Ree.float = re.compile('(?P<price>\d+([{}]\d+)?)'.format(price_sep))

    @staticmethod
    def _is_number():
        Ree.number = re.compile('^\d+$')

    @staticmethod
    def _extract_int_compile():
        Ree.extract_int = re.compile('^.*?(?P<int>\d+).+$')
