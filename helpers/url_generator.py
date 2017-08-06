from urllib import parse
from urllib.parse import urlencode, urljoin


class UrlGenerator:
    # system const, yep
    URL_LIB_FRAGMENT_POS = 4

    def __init__(self, site_url, site_page_param_name):
        self.site_url = site_url.rstrip('/')
        self.site_page_param_name = site_page_param_name

    def get_page(self, page_number):
        return '{}/?{}={}'.format(self.site_url, self.site_page_param_name, page_number)

    @staticmethod
    def get_page_params(host, part, params=None):
        return UrlGenerator._url_append_params(urljoin(host, part), params)

    @staticmethod
    def _url_append_params(url, params):
        if not params:
            return url

        url_parts = list(parse.urlparse(url))
        query = dict(parse.parse_qsl(url_parts[UrlGenerator.URL_LIB_FRAGMENT_POS]))
        query.update(params)

        url_parts[UrlGenerator.URL_LIB_FRAGMENT_POS] = urlencode(query)

        return parse.urlunparse(url_parts)
