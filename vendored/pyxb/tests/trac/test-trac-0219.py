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
xst = '''<?xml version="1.0"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="anything">
    <xs:complexType mixed="true">
      <xs:sequence>
        <xs:any minOccurs="0"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
  <xs:element name="text" type="xs:string"/>
</xs:schema>
'''

code = pyxb.binding.generate.GeneratePython(schema_text=xst)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac0219 (unittest.TestCase):
    def testElement (self):
        xmlt = six.u('<anything><text>eltcontent</text></anything>')
        instance = CreateFromDocument(xmlt)
        self.assertEqual(1, len(instance.wildcardElements()))
        oc = instance.orderedContent()
        self.assertEqual(1, len(oc))
        self.assertTrue(isinstance(oc[0], pyxb.binding.basis.ElementContent))
        i = anything()
        i.append(text('eltcontent'))
        i.validateBinding()
        xmlt = six.u('<anything><text>eltcontent</text></anything>')
        xmld = xmlt.encode('utf-8')
        self.assertEqual(xmld, i.toxml('utf-8', root_only=True))

    def testMixedOnly (self):
        xmlt = six.u('<anything>mixed</anything>')
        instance = CreateFromDocument(xmlt)
        self.assertEqual(0, len(instance.wildcardElements()))
        oc = instance.orderedContent()
        self.assertEqual(1, len(oc))
        self.assertTrue(isinstance(oc[0], pyxb.binding.basis.NonElementContent))
        i = anything()
        i.append('mixed')
        i.validateBinding()
        xmlt = six.u('<anything>mixed</anything>')
        xmld = xmlt.encode('utf-8')
        self.assertEqual(xmld, i.toxml('utf-8', root_only=True))

if __name__ == '__main__':
    unittest.main()
