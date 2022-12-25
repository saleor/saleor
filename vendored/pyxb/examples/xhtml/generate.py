# -*- coding: utf-8 -*-
from __future__ import print_function
import pyxb.bundles.common.xhtml1 as xhtml
import pyxb.utils.domutils

pyxb.utils.domutils.BindingDOMSupport.SetDefaultNamespace(xhtml.Namespace)

head = xhtml.head(title='A Test Document')
body = xhtml.body()
body.append(xhtml.h1('Contents'))
body.append(xhtml.p('''Here is some text.

It doesn't do anything special.'''))

p2 = xhtml.p('Here is more text.  It has ',
             xhtml.b('bold'),
             ' and ',
             xhtml.em('emphasized'),
             ' content with ',
             xhtml.b('more bold'),
             ' just to complicate things.')
body.append(p2)

# Verify we have two b's and an em
assert 2 == len(p2.b)
assert 1 == len(p2.em)

# Generate the document and externally verify that the em is between the two bs.
doc = xhtml.html(head, body)
try:
    xmls = doc.toDOM().toprettyxml()
except pyxb.ValidationError as e:
    print(e.details())
    raise
open('genout.xhtml', 'w').write(xmls)
