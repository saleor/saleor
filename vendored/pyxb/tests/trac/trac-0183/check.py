# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import unittest

import root
import branch1
import branch2

class TestTrac0183 (unittest.TestCase):

    XMLS = '''<ns:msg xmlns:ns="urn:root" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <e3>re3</e3>
  <e1 xmlns="urn:branch1">b1e1</e1>
  <e2 xmlns="urn:branch2">b2e2</e2>
</ns:msg>'''

    def testBasic (self):
        instance = root.CreateFromDocument(self.XMLS)
        self.assertEqual('b1e1', instance.e1)
        self.assertTrue(instance.e1._element(), branch1.e1)
        self.assertEqual('b2e2', instance.e2)
        self.assertTrue(instance.e2._element(), branch2.e2)
        self.assertEqual('re3', instance.e3)
        self.assertTrue(instance.e3._element(), root.msg.typeDefinition()._UseForTag('e3'))

if __name__ == '__main__':
    unittest.main()
