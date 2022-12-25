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
<xs:schema targetNamespace="whatever"
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
'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestBug_200907251353 (unittest.TestCase):
    def testBasic (self):
        anon = [ _s for _s in globals() if _s.startswith('STD_ANON') ]
        self.assertEqual(2, len(anon))

if __name__ == '__main__':
    unittest.main()
