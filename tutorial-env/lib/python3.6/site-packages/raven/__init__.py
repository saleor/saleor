"""
raven
~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

import os
import os.path

__all__ = ('VERSION', 'Client', 'get_version')

VERSION = '6.9.0'


def _get_git_revision(path):
    revision_file = os.path.join(path, 'refs', 'heads', 'master')
    if os.path.exists(revision_file):
        with open(revision_file) as fh:
            return fh.read().strip()[:7]


def get_revision():
    """
    :returns: Revision number of this branch/checkout, if available. None if
        no revision number can be determined.
    """
    package_dir = os.path.dirname(__file__)
    checkout_dir = os.path.normpath(os.path.join(package_dir, os.pardir, os.pardir))
    path = os.path.join(checkout_dir, '.git')
    if os.path.exists(path):
        return _get_git_revision(path)


def get_version():
    base = VERSION
    if __build__:
        base = '%s (%s)' % (base, __build__)
    return base


__build__ = get_revision()
__docformat__ = 'restructuredtext en'


# Declare child imports last to prevent recursion
from raven.base import *  # NOQA
from raven.conf import *  # NOQA
from raven.versioning import *  # NOQA
