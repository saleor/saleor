# -*- coding: utf-8 -*-
from __future__ import print_function
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import time
import pyxb.binding.generate
import pyxb.utils.domutils
from pyxb.utils.six.moves import xrange

max_reps = 20

def buildTest (num_reps, constraint='minOccurs="0" maxOccurs="1"'):
    edefs = []
    cdefs = []
    duse = []
    for r in xrange(num_reps):
        edefs.append('<xs:element name="rep%d" type="xs:string"/>' % (r,))
        cdefs.append('<xs:element ref="rep%d" %s/>' % (r, constraint))
        duse.append('<rep%d>text_%d</rep%d>' % (r, r, r))

    schema = ''.join([ '''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">''',
                   "\n".join(edefs),
                   '''<xs:element name="collection">
<xs:complexType><xs:sequence>''',
                   "\n".join(cdefs),
                   '''</xs:sequence></xs:complexType>
</xs:element>
</xs:schema>''' ])

    xmls = '<collection>' + ''.join(duse) + '</collection>'

    return (schema, xmls)

for size in xrange(1, max_reps):
    (schema, xmls) = buildTest(size)

    t0 = time.time()
    code = pyxb.binding.generate.GeneratePython(schema_text=schema)
    t1 = time.time()
    rv = compile(code, 'test', 'exec')
    t2 = time.time()
    eval(rv)
    t3 = time.time()
    #open('code.py', 'w').write(code)
    #print xmls
    ct0 = time.time()
    doc = CreateFromDocument(xmls)
    ct1 = time.time()

    print("%d gen=%g cpl=%g ld=%g prs=%g" % (size, t1 - t0, t2 - t1, t3 - t2, ct1 - ct0))
    # Should not take more than a second (really, less than 10ms)
    assert (ct1 - ct0) < 1.0
    #open('code.py', 'w').write(code)
