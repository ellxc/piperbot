from collections.abc import MutableMapping, Mapping
from collections import defaultdict

class MutableNameSpace(MutableMapping):
    def __init__(self, data=None, all=False):
        if data is None:
            data = {}
        self._data = data
        self._all = all

    def __repr__(self):
        ret = "{"
        ret += ", ".join(["{}: {}".format(repr(key), repr(val)) for key, val in self._data.items()])
        ret += "}"
        return ret

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def __delitem__(self, key):
        del self._data[key]

    def __delattr__(self, item):
        del self._data[item]

    def setdefault(self, key, default=None):
        if key in self._data:
            return self._data[key]
        else:
            self._data[key] = default

    def copy(self):
        return MutableNameSpace(self._data.copy(), all=self._all)

    def __getattr__(self, item):
        if item in self._data:
            ret = self._data[item]
            if isinstance(ret, MutableMapping) and not isinstance(ret, MutableNameSpace):
                return MutableNameSpace(ret, all=self._all)
            else:
                return ret
        else:
            if self._all:
                self._data[item] = MutableNameSpace({}, all=self._all)
                return self._data[item]
            else:
                raise KeyError('%s' % item)

    def __setattr__(self, key, value):
        if key.startswith("_"):
            object.__setattr__(self, key, value)
        elif isinstance(value, dict):
            return self._data.__setitem__(key, MutableNameSpace(value, all=self._all))
        else:
            return self._data.__setitem__(key, value)

    def __contains__(self, item):
        return item in self._data

    def __getitem__(self, key):
        return self.__getattr__(key)

    def __setitem__(self, key, value):
        return self.__setattr__(key, value)

    def __setstate__(self, vals):
        self._data = vals["data"]
        self._all = vals["all"]

    def __getstate__(self):
        return {
            "data": self._data,
            "all": self._all,
                }


class ReadOnlyNameSpace(Mapping):
    def __init__(self, data=None, all=False):
        if data is None:
            data = {}
        self._data = data
        self._all = all

    def __getattr__(self, item):
        return self.__getitem__(item)

    def __setattr__(self, key, value):
        if key.startswith("_"):
            object.__setattr__(self, key, value)
        else:
            raise AttributeError("Read only")

    def __getitem__(self, key):
        if key in self._data or not self._all:
            ret = self._data[key]
            if self._all and isinstance(ret, MutableNameSpace):
                return ReadOnlyNameSpace(ret._data, all=self._all)
            if isinstance(ret, dict):
                return ReadOnlyNameSpace(ret, all=self._all)
            if isinstance(ret, list):
                return list(ret)
            if isinstance(ret, set):
                return set(ret)
            else:
                return ret
        else:
            raise KeyError('%s' % key)

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def __repr__(self):
        ret = "{"
        ret += ", ".join(["{}: {}".format(repr(key), repr(val)) for key, val in self._data.items()])
        ret += "}"
        return ret

    def __getstate__(self):
        return {
            "data": self._data,
            "all": self._all,
                }

    def __setstate__(self, vals):
        self._data = vals["data"]
        self._all = vals["all"]


bob = {
    "karma": 5,
    "seval": {},
    "general": {
        "foo": "bar",
        "baz": 7,
    }
}

jon = {
    "karma": 5,
    "seval": {},
    "asd": {},
    "general": {
        "foo": "bar",
        "baz": 7,
    }
}

userst = defaultdict(dict, {
    "bob": bob,
    "jon": jon
})


users = MutableNameSpace(userst)
users.jon.channels = []
MutableNameSpace(userst).jon.channels.append("derp")

self = MutableNameSpace({}, all=True)
readonlyusers = ReadOnlyNameSpace(userst, all=True)
