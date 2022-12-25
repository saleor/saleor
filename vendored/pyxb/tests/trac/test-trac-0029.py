# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.utils.domutils
from xml.dom import Node

import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema  xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="elt1" type="xs:string"/>
  <xs:element name="elt2" type="xs:string"/>
  <xs:complexType name="mytype">
     <xs:sequence>
       <xs:element ref="elt1"/>
       <xs:element ref="elt2"/>
     </xs:sequence>
  </xs:complexType>
  <xs:complexType name="mytypeWC">
     <xs:sequence>
       <xs:element ref="elt1"/>
       <xs:element ref="elt2"/>
       <xs:any namespace="##other" processContents="lax"/>
     </xs:sequence>
  </xs:complexType>
</xs:schema>
'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac0029 (unittest.TestCase):
    """Presence of a wildcard in a sequence model group causes other
    elements in that group to not be generated."""
    def test (self):
        self.assertTrue(mytype._UseForTag('elt1') is not None)
        self.assertTrue(mytype._UseForTag('elt2') is not None)

        self.assertTrue(mytypeWC._UseForTag('elt1') is not None)
        self.assertTrue(mytypeWC._UseForTag('elt2') is not None)


if __name__ == '__main__':
    unittest.main()
