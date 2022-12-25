# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import xml.dom.minidom
import pyxb.utils.domutils

import unittest

class TestTrac0156a (unittest.TestCase):
    def testLocateUnique (self):
        dom = xml.dom.minidom.parseString('<xs:simpleType xmlns:xs="http://www.w3.org/2001/XMLSchema"><xs:list>x</xs:list></xs:simpleType>')
        x = pyxb.utils.domutils.LocateUniqueChild (dom.firstChild, 'list')
        dom = xml.dom.minidom.parseString('<xs:simpleType xmlns:xs="http://www.w3.org/2001/XMLSchema"><xs:list>x</xs:list><xs:list>x</xs:list></xs:simpleType>')
        self.assertRaises(pyxb.SchemaValidationError, pyxb.utils.domutils.LocateUniqueChild, dom.firstChild, 'list')
        dom = xml.dom.minidom.parseString('<xs:simpleType xmlns:xs="http://www.w3.org/2001/XMLSchema"><xs:lit>x</xs:lit></xs:simpleType>')
        self.assertRaises(pyxb.SchemaValidationError, pyxb.utils.domutils.LocateUniqueChild, dom.firstChild, 'list', absent_ok=False)

if __name__ == '__main__':
    unittest.main()
