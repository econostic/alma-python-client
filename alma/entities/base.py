from copy import deepcopy


class Base:
    def __init__(self, data):
        self._data = data

    def __getattr__(self, key):
        if not key in self._data:
            raise AttributeError(key)
        return self._data[key]

    @property
    def raw_data(self):
        return self._data
