from urllib import parse

from d_parser.helpers.logger_overrider import Log


class LinkStore:
    def __init__(self, log: Log, warn_limit_after: int = 1):
        self._links = {}
        self._log = log
        self._limit = warn_limit_after

    @property
    def data(self) -> []:
        return self._links

    def get(self, url: str) -> int:
        return self._links.get(url, 0)

    def add(self, url: str, remove_fragment: bool = True) -> bool:
        if remove_fragment:
            url = parse.urldefrag(url).url

        count = self._links.get(url, 0)
        self._log.debug(f'Add link: {url} [count: {count}]')

        self._links[url] = count + 1

        return self._links[url] > self._limit
