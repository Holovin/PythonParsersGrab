from d_parser.helpers.logger_overrider import Log


class DataContainer:
    def __init__(self, log: Log = None):
        self._data = []
        self.log = log

        # some optimizations
        if self.log:
            self.add = self._add_log
        else:
            self.add = self._add

    @property
    def data(self) -> []:
        return self._data

    def append(self, anything):
        self.log.fatal('\nvvv\n >>> Method .append is obsolete, use .add <<<\n ^^^\n')

    def _add(self, data_object: {}) -> None:
        self._data.append(data_object)

    def _add_log(self, data_object: {}) -> None:
        self._data.append(data_object)
        self.log.info('Add item: {}'.format(data_object))
