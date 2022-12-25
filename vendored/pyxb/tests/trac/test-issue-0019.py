# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.utils.domutils
from pyxb.utils import six
from xml.dom import Node
import pyxb.namespace
import xml.dom.minidom as minidom

import os.path
xst = '''<?xml version="1.0" encoding="utf-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="elt" type="xs:string"/>
</xs:schema>
'''


code = pyxb.binding.generate.GeneratePython(schema_text=xst)
#open('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

import copy

class TestIssue19 (unittest.TestCase):
    def testCopy (self):
        x = elt('shallow')
        # This one doesn't generate a warning
        x2 = copy.copy(x)
        self.assertEqual(x, x2)
        self.assertNotEqual(id(x), id(x2))
        self.assertEqual('shallow', x2)

    def testDeepCopy (self):
        x = elt('deep')
        # This one does generate a warning
        x2 = copy.deepcopy(x)
        self.assertEqual(x, x2)
        self.assertNotEqual(id(x), id(x2))
        self.assertEqual('deep', x2)

if __name__ == '__main__':
    unittest.main()
