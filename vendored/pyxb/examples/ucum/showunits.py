# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import ucum
import pyxb
import sys
from pyxb.utils import six

def ucumHTML (u):
    """Convert mixed content to UCUM's version of HTML"""
    txt = []
    if isinstance(u, six.text_type):
        return u.strip()
    for c in u.orderedContent():
        if isinstance(c, pyxb.binding.basis.NonElementContent):
            txt.append(c.value.strip())
        else:
            en = c.value._element().name().localName()
            txt.append('<{}>{}</{}>'.format(en, ucumHTML(c.value), en))
    return ''.join(txt)

try:
    instance = ucum.CreateFromDocument(open('ucum-essence.xml').read())
except pyxb.ValidationError as e:
    print(e.details())
    sys.exit(1)

units = []
units.extend(instance.base_unit)
units.extend(instance.unit)
for u in units:
    if isinstance(u, ucum.base_unit.typeDefinition()):
        print(u.Code)
    elif 1 == u.value_.value_:
        print('{}\talias {}'.format(u.Code, u.value_.Unit))
    elif u.value_.function is not None:
        print('{}\tas value {}'.format(u.Code, u.value_.Unit))
    else:
        print('{}\tas {} times {}'.format(u.Code, u.value_.value_, u.value_.Unit))
    ps = ''
    if u.printSymbol is not None:
        ps = ucumHTML(u.printSymbol)
    if ps:
        print('\tprints as: {}'.format(ps))
