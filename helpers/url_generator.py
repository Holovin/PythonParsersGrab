class UrlGenerator:
    def __init__(self, site_url, site_page_param_name):
        self.site_url = site_url.rstrip('/')
        self.site_page_param_name = site_page_param_name

    def get_page(self, page_number):
        return '{}/?{}={}'.format(self.site_url, self.site_page_param_name, page_number)
