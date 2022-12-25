# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.binding.datatypes as xs
import pyxb.binding.basis
import pyxb.utils.domutils
from pyxb.utils import six

import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:tns="urn:trac-0069" targetNamespace="urn:trac-0069">
  <xs:element name="MetadataDocument" type="tns:MetadataType"/>
  <xs:complexType name="MetadataType">
    <xs:sequence maxOccurs="1" minOccurs="1">
      <xs:element name="template" type="xs:string"/>
      <xs:element name="timespan" maxOccurs="unbounded" minOccurs="0">
        <xs:complexType>
          <xs:sequence>
            <xs:element name="field" maxOccurs="unbounded" minOccurs="0">
              <xs:complexType>
                <xs:sequence>
                  <xs:element name="name" type="xs:string"/>
                  <xs:element name="value" minOccurs="0" maxOccurs="unbounded">
                    <xs:complexType>
                      <xs:simpleContent>
                        <xs:extension base="xs:string">
                          <xs:attribute name="lang" type="xs:language"/>
                          <xs:attribute name="user" type="xs:string"/>
                          <xs:attribute name="timestamp" type="xs:dateTime"/>
                        </xs:extension>
                      </xs:simpleContent>
                    </xs:complexType>
                  </xs:element>
                </xs:sequence>
                <xs:attribute name="track" type="xs:string"/>
              </xs:complexType>
            </xs:element>
          </xs:sequence>
          <xs:attribute name="start" type="xs:string"/>
          <xs:attribute name="end" type="xs:string"/>
        </xs:complexType>
      </xs:element>
    </xs:sequence>
  </xs:complexType>
</xs:schema>
'''

#open('schema.xsd', 'w').write(xsd)
code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest
import collections

# Pretend whoever created the schema was helpful and had normalized it
metadatadoc_type = MetadataDocument.typeDefinition()
timespan_element = metadatadoc_type._ElementMap['timespan'].elementBinding()
timespan_type = timespan_element.typeDefinition()
field_element = timespan_type._ElementMap['field'].elementBinding()
field_type = field_element.typeDefinition()
value_element = field_type._ElementMap['value'].elementBinding()
value_type = value_element.typeDefinition()

v_bind = pyxb.BIND('foo', lang='ENG')

class TestTrac_0069 (unittest.TestCase):
    def testMetaConstructor (self):
        newdoc = MetadataDocument()
        newdoc.template = 'anewtemplate'

        newdoc.timespan.append(pyxb.BIND(start='-INF', end='+INF'))
        timespan = newdoc.timespan[0]
        self.assertTrue(isinstance(timespan, timespan_type))
        timespan.field.append(pyxb.BIND('name', pyxb.BIND('fv0'), pyxb.BIND('fv1')))
        field = timespan.field[0]
        self.assertTrue(isinstance(field, field_type))
        field.value_.append('fv2')
        fv2 = field.value_[2]
        self.assertTrue(isinstance(fv2, value_type))
        self.assertEqual('fv2', fv2.value())
        newdoc.validateBinding()
        xmlt = six.u('<ns1:MetadataDocument xmlns:ns1="urn:trac-0069"><template>anewtemplate</template><timespan end="+INF" start="-INF"><field><name>name</name><value>fv0</value><value>fv1</value><value>fv2</value></field></timespan></ns1:MetadataDocument>')
        xmld = xmlt.encode('utf-8')
        self.assertEqual(newdoc.toxml("utf-8", root_only=True), xmld)

if __name__ == '__main__':
    unittest.main()
