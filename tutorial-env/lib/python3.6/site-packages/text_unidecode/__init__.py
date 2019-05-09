# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import os
import pkgutil

_replaces = pkgutil.get_data(__name__, 'data.bin').decode('utf8').split('\x00')

def unidecode(txt):
    chars = []
    for ch in txt:
        codepoint = ord(ch)

        if not codepoint:
            chars.append('\x00')
            continue

        try:
            chars.append(_replaces[codepoint-1])
        except IndexError:
            pass
    return "".join(chars)
