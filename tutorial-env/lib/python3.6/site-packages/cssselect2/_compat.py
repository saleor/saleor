try:
    basestring = basestring
except NameError:
    basestring = str

try:
    from itertools import ifilter
except ImportError:
    ifilter = filter
