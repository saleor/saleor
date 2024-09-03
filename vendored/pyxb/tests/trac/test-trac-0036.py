# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.binding.datatypes as xs
import pyxb.binding.basis
import pyxb.utils.domutils

import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="B" type="xs:byte"/>
  <xs:element name="I" type="xs:int"/>
  <xs:element name="D" type="xs:double"/>
  <xs:group name="types">
     <xs:choice maxOccurs="unbounded">
        <xs:element ref="B"/>
        <xs:element ref="I"/>
        <xs:element ref="D"/>
     </xs:choice>
  </xs:group>
  <xs:complexType name="tData">
    <xs:sequence>
      <xs:group ref="types"/>
    </xs:sequence>
  </xs:complexType>
  <xs:element name="data" type="tData"/>
</xs:schema>'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac_200908041715 (unittest.TestCase):
    # Verify that we can reconstruct the element associated with
    # content values.

    def testKeyword (self):
        instance = data(B=4)
        self.assertEqual(1, len(instance.orderedContent()))
        cv = instance.orderedContent()[0]
        self.assertEqual(4, cv.value)
        self.assertEqual(cv.value._element(), tData._ElementMap['B'].elementBinding())

        instance = data(I=4)
        self.assertEqual(1, len(instance.orderedContent()))
        cv = instance.orderedContent()[0]
        self.assertEqual(4, cv.value)
        self.assertEqual(cv.value._element(), tData._ElementMap['I'].elementBinding())

    def testValue (self):
        instance = data(4)
        self.assertEqual(1, len(instance.orderedContent()))
        cv = instance.orderedContent()[0]
        self.assertEqual(cv.value._element(), tData._ElementMap['B'].elementBinding())

        instance = data(300)
        self.assertEqual(1, len(instance.orderedContent()))
        cv = instance.orderedContent()[0]
        self.assertEqual(cv.value._element(), tData._ElementMap['I'].elementBinding())

        instance = data(42.3)
        self.assertEqual(1, len(instance.orderedContent()))
        cv = instance.orderedContent()[0]
        self.assertEqual(cv.value._element(), tData._ElementMap['D'].elementBinding())

if __name__ == '__main__':
    unittest.main()
