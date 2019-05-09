"""This module contains general utility code that is used throughout
the library.

For users of this library, the C{L{log}} function is probably the most
interesting.
"""

__all__ = [
    'log', 'appendArgs', 'toBase64', 'fromBase64', 'autoSubmitHTML',
    'toUnicode'
]

import binascii
import logging

# import urllib.parse as urlparse
from urllib.parse import urlencode

xxe_safe_elementtree_modules = [
    'defusedxml.cElementTree',
    'defusedxml.ElementTree',
]

elementtree_modules = [
    'xml.etree.cElementTree',
    'xml.etree.ElementTree',
    'cElementTree',
    'elementtree.ElementTree',
]


def toUnicode(value):
    """Returns the given argument as a unicode object.

    @param value: A UTF-8 encoded string or a unicode (coercable) object
    @type message: str or unicode

    @returns: Unicode object representing the input value.
    """
    if isinstance(value, bytes):
        return value.decode('utf-8')
    return str(value)


def autoSubmitHTML(form, title='OpenID transaction in progress'):
    if isinstance(form, bytes):
        form = str(form, encoding="utf-8")
    if isinstance(title, bytes):
        title = str(title, encoding="utf-8")
    html = """
<html>
<head>
  <title>%s</title>
</head>
<body onload="document.forms[0].submit();">
%s
<script>
var elements = document.forms[0].elements;
for (var i = 0; i < elements.length; i++) {
  elements[i].style.display = "none";
}
</script>
</body>
</html>
""" % (title, form)
    return html


def importSafeElementTree(module_names=None):
    """Find a working ElementTree implementation that is not vulnerable
    to XXE, using `defusedxml`.

    >>> XXESafeElementTree = importSafeElementTree()

    @param module_names: The names of modules to try to use as
        a safe ElementTree. Defaults to C{L{xxe_safe_elementtree_modules}}

    @returns: An ElementTree module that is not vulnerable to XXE.
    """
    if module_names is None:
        module_names = xxe_safe_elementtree_modules
    try:
        return importElementTree(module_names)
    except ImportError:
        raise ImportError('Unable to find a ElementTree module '
                          'that is not vulnerable to XXE. '
                          'Tried importing %r' % (module_names, ))


def importElementTree(module_names=None):
    """Find a working ElementTree implementation, trying the standard
    places that such a thing might show up.

    >>> ElementTree = importElementTree()

    @param module_names: The names of modules to try to use as
        ElementTree. Defaults to C{L{elementtree_modules}}

    @returns: An ElementTree module
    """
    if module_names is None:
        module_names = elementtree_modules

    for mod_name in module_names:
        try:
            ElementTree = __import__(mod_name, None, None, ['unused'])
        except ImportError:
            pass
        else:
            # Make sure it can actually parse XML
            try:
                ElementTree.XML('<unused/>')
            except (SystemExit, MemoryError, AssertionError):
                raise
            except:
                logging.exception(
                    'Not using ElementTree library %r because it failed to '
                    'parse a trivial document: %s' % mod_name)
            else:
                return ElementTree
    else:
        raise ImportError('No ElementTree library found. '
                          'You may need to install one. '
                          'Tried importing %r' % (module_names, ))


def log(message, level=0):
    """Handle a log message from the OpenID library.

    This is a legacy function which redirects to logging.error.
    The logging module should be used instead of this

    @param message: A string containing a debugging message from the
        OpenID library
    @type message: str

    @param level: The severity of the log message. This parameter is
        currently unused, but in the future, the library may indicate
        more important information with a higher level value.
    @type level: int or None

    @returns: Nothing.
    """

    logging.error("This is a legacy log message, please use the "
                  "logging module. Message: %s", message)


def appendArgs(url, args):
    """Append query arguments to a HTTP(s) URL. If the URL already has
    query arguemtns, these arguments will be added, and the existing
    arguments will be preserved. Duplicate arguments will not be
    detected or collapsed (both will appear in the output).

    @param url: The url to which the arguments will be appended
    @type url: str

    @param args: The query arguments to add to the URL. If a
        dictionary is passed, the items will be sorted before
        appending them to the URL. If a sequence of pairs is passed,
        the order of the sequence will be preserved.
    @type args: A dictionary from string to string, or a sequence of
        pairs of strings.

    @returns: The URL with the parameters added
    @rtype: str
    """
    if hasattr(args, 'items'):
        args = sorted(args.items())
    else:
        args = list(args)

    if not isinstance(url, str):
        url = str(url, encoding="utf-8")

    if not args:
        return url

    if '?' in url:
        sep = '&'
    else:
        sep = '?'

    # Map unicode to UTF-8 if present. Do not make any assumptions
    # about the encodings of plain bytes (str).
    i = 0
    for k, v in args:
        if not isinstance(k, bytes):
            k = k.encode('utf-8')

        if not isinstance(v, bytes):
            v = v.encode('utf-8')

        args[i] = (k, v)
        i += 1

    return '%s%s%s' % (url, sep, urlencode(args))


def toBase64(s):
    """Represent string / bytes s as base64, omitting newlines"""
    if isinstance(s, str):
        s = s.encode("utf-8")
    return binascii.b2a_base64(s)[:-1]


def fromBase64(s):
    if isinstance(s, str):
        s = s.encode("utf-8")
    try:
        return binascii.a2b_base64(s)
    except binascii.Error as why:
        # Convert to a common exception type
        raise ValueError(str(why))


class Symbol(object):
    """This class implements an object that compares equal to others
    of the same type that have the same name. These are distict from
    str or unicode objects.
    """

    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        return type(self) is type(other) and self.name == other.name

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash((self.__class__, self.name))

    def __repr__(self):
        return '<Symbol %s>' % (self.name, )
