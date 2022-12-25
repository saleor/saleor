# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.binding.datatypes as xs
import pyxb.binding.basis
import pyxb.utils.domutils

whatever = 'whatever200908021351'
import os.path
decl_xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema targetNamespace="%s"
  xmlns:whatever="whatever"
  xmlns:xs="http://www.w3.org/2001/XMLSchema">

 <xs:attribute name="lang">
  <xs:simpleType>
   <xs:union memberTypes="xs:language">
    <xs:simpleType>
     <xs:restriction base="xs:string">
      <xs:enumeration value=""/>
     </xs:restriction>
    </xs:simpleType>
   </xs:union>
  </xs:simpleType>
 </xs:attribute>
</xs:schema>
''' % (whatever,)

use_xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:whatever="%s">

 <xs:complexType name="ctd">
  <xs:attribute ref="whatever:lang"/>
 </xs:complexType>
</xs:schema>
''' % (whatever,)

import unittest

class TestBug_200908021351 (unittest.TestCase):
    def testBasic (self):
        generator = pyxb.binding.generate.Generator(allow_absent_module=True, generate_to_files=False)
        generator.addSchema(decl_xsd)
        generator.addModuleName('decl')
        generator.addSchema(use_xsd)
        generator.addModuleName('use')
        modules = generator.bindingModules()
        self.assertEqual(2, len(modules))
        ns = pyxb.namespace.NamespaceForURI(whatever)
        self.assertTrue(ns is not None)
        ad = ns.createExpandedName('lang').attributeDeclaration()
        self.assertTrue(ad is not None)
        self.assertEqual(2, len(ad.typeDefinition().memberTypeDefinitions()))

if __name__ == '__main__':
    unittest.main()
