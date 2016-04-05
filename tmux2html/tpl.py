import os
from string import Template


_cache = {}
_basedir = os.path.dirname(__file__)


def load(name):
    """Load a template and cache it.
    """
    if name in _cache:
        return _cache.get(name)

    with open(os.path.join(_basedir, 'templates', name), 'rt') as fp:
        _cache[name] = Template(fp.read())

    return _cache.get(name)


def render(name, **kwargs):
    return load(name).safe_substitute(**kwargs)
