# defusedxml
#
# Copyright (c) 2013 by Christian Heimes <christian@python.org>
# Licensed to PSF under a Contributor Agreement.
# See https://www.python.org/psf/license for licensing details.
"""Defuse XML bomb denial of service vulnerabilities
"""
from __future__ import print_function, absolute_import

from .common import (
    DefusedXmlException,
    DTDForbidden,
    EntitiesForbidden,
    ExternalReferenceForbidden,
    NotSupportedError,
    _apply_defusing,
)


def defuse_stdlib():
    """Monkey patch and defuse all stdlib packages

    :warning: The monkey patch is an EXPERIMETNAL feature.
    """
    defused = {}

    from . import cElementTree
    from . import ElementTree
    from . import minidom
    from . import pulldom
    from . import sax
    from . import expatbuilder
    from . import expatreader
    from . import xmlrpc

    xmlrpc.monkey_patch()
    defused[xmlrpc] = None

    for defused_mod in [
        cElementTree,
        ElementTree,
        minidom,
        pulldom,
        sax,
        expatbuilder,
        expatreader,
    ]:
        stdlib_mod = _apply_defusing(defused_mod)
        defused[defused_mod] = stdlib_mod

    return defused


__version__ = "0.6.0"

__all__ = [
    "DefusedXmlException",
    "DTDForbidden",
    "EntitiesForbidden",
    "ExternalReferenceForbidden",
    "NotSupportedError",
]
