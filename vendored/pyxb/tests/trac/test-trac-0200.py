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
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="xdateTime" nillable="true" type="xs:dateTime"/>
  <xs:element name="xdate" nillable="true" type="xs:date"/>
  <xs:element name="xtime" nillable="true" type="xs:time"/>
  <xs:element name="xboolean" nillable="true" type="xs:boolean"/>
  <xs:element name="xduration" nillable="true" type="xs:duration"/>
</xs:schema>
'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac0200 (unittest.TestCase):

    def testFull_dateTime (self):
        instance = CreateFromDocument('<xdateTime>2006-05-04T18:13:51.0Z</xdateTime>')
        self.assertFalse(instance._isNil())

    def testNil_dateTime (self):
        instance = CreateFromDocument('<xdateTime xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:nil="true"/>')
        self.assertTrue(instance._isNil())

    def testFull_date (self):
        instance = CreateFromDocument('<xdate>2006-05-04</xdate>')
        self.assertFalse(instance._isNil())

    def testNil_date (self):
        instance = CreateFromDocument('<xdate xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:nil="true"/>')
        self.assertTrue(instance._isNil())

    def testFull_time (self):
        instance = CreateFromDocument('<xtime>18:13:51.0Z</xtime>')
        self.assertFalse(instance._isNil())

    def testNil_time (self):
        instance = CreateFromDocument('<xtime xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:nil="true"/>')
        self.assertTrue(instance._isNil())

    def testFull_boolean (self):
        instance = CreateFromDocument('<xboolean>true</xboolean>')
        self.assertFalse(instance._isNil())

    def testNil_boolean (self):
        instance = CreateFromDocument('<xboolean xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:nil="true"/>')
        self.assertTrue(instance._isNil())

    def testFull_duration (self):
        instance = CreateFromDocument('<xduration>P3D</xduration>')
        self.assertFalse(instance._isNil())

    def testNil_duration (self):
        instance = CreateFromDocument('<xduration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:nil="true"/>')
        self.assertTrue(instance._isNil())

if __name__ == '__main__':
    unittest.main()
