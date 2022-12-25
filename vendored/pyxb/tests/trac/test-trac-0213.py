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
  <xs:complexType name="tInt">
    <xs:simpleContent>
      <xs:extension base="xs:int">
        <xs:attribute name="units" type="xs:string"/>
      </xs:extension>
    </xs:simpleContent>
  </xs:complexType>
  <xs:element name="Int" type="tInt"/>
</xs:schema>
'''

code = pyxb.binding.generate.GeneratePython(schema_text=xst)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac0213 (unittest.TestCase):
    def testMissingContent (self):
        import copy

        xmlt = six.u('<Int units="m">32</Int>')
        xmld = xmlt.encode('utf-8')
        instance = CreateFromDocument(xmlt)
        self.assertEqual(instance.toxml('utf-8', root_only=True), xmld)
        self.assertEqual(instance.value(), 32)
        self.assertEqual(instance.units, "m")

        ni = copy.copy(instance)
        self.assertEqual(ni.toxml('utf-8', root_only=True), xmld)
        self.assertEqual(ni.value(), 32)
        self.assertEqual(ni.units, "m")
        ni.reset()
        if sys.version_info[:2] < (2, 7):
            self.assertRaises(SimpleContentAbsentError, ni.validateBinding)
        else:
            with self.assertRaises(SimpleContentAbsentError) as cm:
                ni.validateBinding()
            e = cm.exception
            self.assertEqual(e.instance, ni)

if __name__ == '__main__':
    unittest.main()
