# coding=utf-8

from __future__ import unicode_literals
from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):
    # Currently this is my own work
    license_formats = (
        '? ### ??',
        '? ### ???',
        '?? ### ??',
        '?? ### ???',
        '? #### ??',
        '? #### ???',
        '?? #### ??',
        '?? #### ???',
    )
