# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.binding.datatypes as xs
import pyxb.binding.basis
import pyxb.utils.domutils
import sys

# Thanks to agrimstrup for this example

import os.path
xsd='''
<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema" elementFormDefault="qualified" attributeFormDefault="unqualified" version="8 1.87" targetNamespace="URN:test-trac-0057">

  <xsd:element name="ObsProject">
    <xsd:complexType>
      <xsd:sequence>
        <xsd:element name="assignedPriority" type="xsd:int"/>
        <xsd:element name="timeOfCreation" type="xsd:string"/>
      </xsd:sequence>
      <xsd:attribute name="schemaVersion" type="xsd:string" use="required" fixed="8"/>
      <xsd:attribute name="revision" type="xsd:string" default="1.87"/>
      <xsd:attribute name="almatype" type="xsd:string" use="required" fixed="APDM::ObsProject"/>
    </xsd:complexType>
  </xsd:element>


</xsd:schema>
'''

#open('schema.xsd', 'w').write(xsd)
code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac_0057 (unittest.TestCase):
    XMLs = '<ns1:ObsProject almatype="APDM::ObsProject" revision="1.74" schemaVersion="8" xmlns:ns1="URN:test-trac-0057"><ns1:timeOfCreation>2009-05-08 21:23:45</ns1:timeOfCreation></ns1:ObsProject>'
    XMLd = XMLs.encode('utf-8')

    def exec_toxmld (self, v):
        return v.toxml("utf-8")

    def tearDown (self):
        pyxb.RequireValidWhenGenerating(True)
        pyxb.RequireValidWhenParsing(True)

    def testDefault (self):
        self.assertTrue(pyxb._GenerationRequiresValid)
        self.assertTrue(pyxb._ParsingRequiresValid)
        self.assertRaises(pyxb.UnrecognizedContentError, CreateFromDocument, self.XMLs)
        doc = pyxb.utils.domutils.StringToDOM(self.XMLs)
        self.assertRaises(pyxb.UnrecognizedContentError, CreateFromDOM, doc)
        if sys.version_info[:2] >= (2, 7):
            with self.assertRaises(UnrecognizedContentError) as cm:
                CreateFromDocument(self.XMLs)
            # Verify the exception tells us what was being processed
            self.assertTrue(isinstance(cm.exception.instance, ObsProject.typeDefinition()))
            # Verify the exception tells us what was rejected
            time_of_creation_ed = ObsProject.typeDefinition()._UseForTag(Namespace.createExpandedName('timeOfCreation'))
            self.assertTrue(isinstance(cm.exception.value, time_of_creation_ed.elementBinding().typeDefinition()))
            # Verify the exception tells us what would be acceptable
            accept = cm.exception.automaton_configuration.acceptableContent()
            self.assertEqual(1, len(accept))
            assigned_priority_ed = ObsProject.typeDefinition()._UseForTag(Namespace.createExpandedName('assignedPriority'))
            self.assertEqual(accept[0].elementDeclaration(), assigned_priority_ed)

    def testDisable (self):
        pyxb.RequireValidWhenParsing(False)
        instance = CreateFromDocument(self.XMLs)
        self.assertRaises(pyxb.IncompleteElementContentError, self.exec_toxmld, instance)
        if sys.version_info[:2] >= (2, 7):
            with self.assertRaises(IncompleteElementContentError) as cm:
                instance.toxml('utf-8', root_only=True)
            # Verify the exception tells us what was being processed
            self.assertEqual(instance, cm.exception.instance)
            # Verify the exception tells us what would be acceptable
            accept = cm.exception.fac_configuration.acceptableSymbols()
            self.assertEqual(1, len(accept))
            assigned_priority_ed = ObsProject.typeDefinition()._UseForTag(Namespace.createExpandedName('assignedPriority'))
            self.assertEqual(accept[0].elementDeclaration(), assigned_priority_ed)
            # Verify the exception tells us what was left
            time_of_creation_ed = ObsProject.typeDefinition()._UseForTag(Namespace.createExpandedName('timeOfCreation'))
            self.assertEqual(instance.timeOfCreation, cm.exception.symbol_set[time_of_creation_ed][0])

        doc = pyxb.utils.domutils.StringToDOM(self.XMLs)
        instance = CreateFromDOM(doc)
        pyxb.RequireValidWhenGenerating(False)
        xmld = instance.toxml("utf-8", root_only=True)
        self.assertEqual(xmld, self.XMLd)

if __name__ == '__main__':
    unittest.main()
