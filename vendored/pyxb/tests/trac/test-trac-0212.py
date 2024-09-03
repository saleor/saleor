# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.utils.domutils
from pyxb.utils import six
from xml.dom import Node

import os.path
xst = '''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:complexType name="tMixed" mixed="true">
    <xs:sequence>
      <xs:element name="mString" type="xs:string"/>
    </xs:sequence>
  </xs:complexType>
  <xs:element name="Mixed" type="tMixed"/>
</xs:schema>
'''

code = pyxb.binding.generate.GeneratePython(schema_text=xst)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac0212 (unittest.TestCase):

    def testBasicMixed (self):
        xmlt = six.u('<Mixed><mString>body</mString></Mixed>')
        xmld = xmlt.encode('utf-8')
        instance = CreateFromDocument(xmld)
        self.assertEqual(instance.toxml('utf-8', root_only=True), xmld)
        xmlt = six.u('<Mixed>pre<mString>body</mString>post</Mixed>')
        xmld = xmlt.encode('utf-8')
        instance = CreateFromDocument(xmld)
        self.assertEqual(instance.toxml('utf-8', root_only=True), xmld)
        oc = instance.orderedContent()
        self.assertEqual(3, len(oc))
        self.assertEqual(six.u('pre'), oc[0].value)
        self.assertEqual(instance.mString, oc[1].value)
        self.assertEqual(six.u('post'), oc[2].value)
        nec = list(pyxb.NonElementContent(instance))
        self.assertEqual(2, len(nec))
        self.assertEqual(nec[0], six.u('pre'))
        self.assertEqual(nec[1], six.u('post'))
        self.assertEqual(six.u('prepost'), ''.join(pyxb.NonElementContent(instance)))

if __name__ == '__main__':
    unittest.main()
