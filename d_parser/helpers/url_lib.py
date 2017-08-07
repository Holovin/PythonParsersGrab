import urllib.parse


def get_host_from_url(url):
    return '{uri.scheme}://{uri.netloc}/'.format(uri=urllib.parse.urlparse(url))
