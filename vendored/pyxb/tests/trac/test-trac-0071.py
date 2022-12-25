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
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:tns="urn:trac-0071" targetNamespace="urn:trac-0071">
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

class TestTrac_0071 (unittest.TestCase):
    def testFieldConstructor (self):
        field = field_type('title', pyxb.BIND('foo', lang='ENG'), _element=field_element)
        self.assertTrue(isinstance(field.value_, collections.MutableSequence))
        self.assertEqual(1, len(field.value_))
        self.assertTrue(isinstance(field.value_[0], value_type))
        field.validateBinding()
        xmlt = six.u('<field><name>title</name><value lang="ENG">foo</value></field>')
        xmld = xmlt.encode('utf-8')
        self.assertEqual(field.toxml("utf-8", root_only=True), xmld)

    def testFieldElementAppend (self):
        newdoc = MetadataDocument()
        newdoc.template = 'anewtemplate'

        field = field_type(name='title', _element=field_element)
        field.value_.append(pyxb.BIND('foo', lang='ENG'))
        self.assertTrue(isinstance(field.value_, collections.MutableSequence))
        self.assertEqual(1, len(field.value_))
        self.assertTrue(isinstance(field.value_[0], value_type))
        field.validateBinding()
        self.assertTrue(isinstance(field.value_[0], value_type))
        xmlt = six.u('<field><name>title</name><value lang="ENG">foo</value></field>')
        xmld = xmlt.encode('utf-8')
        self.assertEqual(field.toxml("utf-8", root_only=True), xmld)

    MetaExpectedt = '<ns1:MetadataDocument xmlns:ns1="urn:trac-0071"><template>anewtemplate</template><timespan end="+INF" start="-INF"><field><name>title</name><value lang="ENG">foo</value></field></timespan></ns1:MetadataDocument>'
    MetaExpectedd = MetaExpectedt.encode('utf-8')

    def testMetaConstructor (self):
        newdoc = MetadataDocument()
        newdoc.template = 'anewtemplate'

        newdoc.timespan.append(pyxb.BIND( # Single timespan
                pyxb.BIND( # First field instance
                    'title',
                    pyxb.BIND('foo', lang='ENG')
                    ),
                start='-INF', end='+INF'))
        timespan = newdoc.timespan[0]
        self.assertTrue(isinstance(timespan, timespan_type))
        newdoc.validateBinding()
        timespan = newdoc.timespan[0]
        self.assertTrue(isinstance(timespan, timespan_type))
        self.assertEqual(self.MetaExpectedd, newdoc.toxml("utf-8", root_only=True))
        newdoc.timespan[:] = []

    def testMetaBadFieldName (self):
        newdoc = MetadataDocument()
        newdoc.template = 'anewtemplate'

        v_bind = pyxb.BIND('foo', lang='ENG')

        # This binding is wrong: the field name is "value_" not "value"
        f_bind = pyxb.BIND(name='title', value=v_bind)
        ts_bind = pyxb.BIND(f_bind, start='-INF', end='+INF')
        if sys.version_info[:2] < (2, 7):
            self.assertRaises(pyxb.UnrecognizedContentError, newdoc.timespan.append, ts_bind)
            return
        with self.assertRaises(pyxb.UnrecognizedContentError) as cm:
            newdoc.timespan.append(ts_bind)
        self.assertEqual(f_bind, cm.exception.value)

    def testMetaBadPlurality (self):
        newdoc = MetadataDocument()
        newdoc.template = 'anewtemplate'

        # This binding is wrong: the field "value_" is plural and the
        # value for the keyword must be iterable.
        f_bind = pyxb.BIND(name='title', value_=v_bind)
        ts_bind = pyxb.BIND(f_bind, start='-INF', end='+INF')
        if sys.version_info[:2] < (2, 7):
            self.assertRaises(pyxb.UnrecognizedContentError, newdoc.timespan.append, ts_bind)
            return
        with self.assertRaises(pyxb.UnrecognizedContentError) as cm:
            newdoc.timespan.append(ts_bind)
        self.assertEqual(f_bind, cm.exception.value)

    def testMetaGoodBind (self):
        newdoc = MetadataDocument()
        newdoc.template = 'anewtemplate'

        # This one should be OK
        bind = pyxb.BIND( # First field instance
                    name='title',
                    value_=[pyxb.BIND('foo', lang='ENG')]
                    )
        newdoc.timespan.append(pyxb.BIND(bind, start='-INF', end='+INF'))
        timespan = newdoc.timespan[0]
        self.assertTrue(isinstance(timespan, timespan_type))
        newdoc.validateBinding()
        self.assertEqual(self.MetaExpectedd, newdoc.toxml("utf-8", root_only=True))

if __name__ == '__main__':
    unittest.main()
