# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import sys
import unittest

class TestTrac0099a (unittest.TestCase):
    def setUp (self):
        # Hide the error about failure to check value constraint
        self.__structures_log = logging.getLogger('pyxb.xmlschema.structures')
        self.__structures_loglevel = self.__structures_log.level
        self.__structures_log.setLevel(logging.CRITICAL)

    def tearDown (self):
        pyxb.RequireValidWhenParsing(True)
        self.__structures_log.level = self.__structures_loglevel

    def testRefWithAttrs (self):
        xsd = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="uncs" type="xs:string"/>
  <xs:element name="complex">
    <xs:complexType>
      <xs:sequence>
        <xs:element ref="uncs" default="value"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>'''
        self.assertRaises(pyxb.SchemaValidationError, pyxb.binding.generate.GeneratePython, schema_text=xsd)

    def testConstraintOnComplex (self):
        xsd = '''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="complex" default="foo">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="elt" type="xs:string"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>'''
        if sys.version_info[:2] < (2, 7):
            self.assertRaises(pyxb.SchemaValidationError, pyxb.binding.generate.GeneratePython, schema_text=xsd)
            return
        with self.assertRaises(pyxb.SchemaValidationError) as cm:
            code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
        self.assertEqual('Value constraint on element complex with non-simple content', str(cm.exception))

if __name__ == '__main__':
    unittest.main()
