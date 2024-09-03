# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb
import pyxb.binding.generate
import pyxb.utils.domutils

from xml.dom import Node

import os.path
schema_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../schemas/test-recursive.xsd'))
code = pyxb.binding.generate.GeneratePython(schema_location=schema_path)

rv = compile(code, 'test', 'exec')
eval(rv)

import unittest

class TestXSIType (unittest.TestCase):
    def testSingleton (self):
        xml = '<node><data>singleton</data></node>'
        doc = pyxb.utils.domutils.StringToDOM(xml)
        instance = node.createFromDOM(doc.documentElement)
        self.assertEqual('singleton', instance.data)
        self.assertTrue(instance.left is None)
        self.assertTrue(instance.right is None)

        instance = node('singleton')
        self.assertEqual('singleton', instance.data)
        self.assertTrue(instance.left is None)
        self.assertTrue(instance.right is None)

    def testLeftOnly (self):
        xml = '<node><data>root</data><left><data>left</data></left></node>'
        doc = pyxb.utils.domutils.StringToDOM(xml)
        instance = node.createFromDOM(doc.documentElement)
        self.assertEqual('root', instance.data)
        left = instance.left
        self.assertTrue(left is not None)
        self.assertEqual('left', left.data)
        self.assertTrue(instance.right is None)

        instance = node('root', node('left'))
        self.assertEqual('root', instance.data)
        left = instance.left
        self.assertTrue(left is not None)
        self.assertEqual('left', left.data)
        self.assertTrue(instance.right is None)

    def testFiver (self):
        instance = node('root', node('left1', node('left2'), node('leftright')), node('right1', node('rightleft')))
        xml = '<node><data>root</data><left><data>left1</data><left><data>left2</data></left><right><data>leftright</data></right></left><right><data>right1</data><left><data>rightleft</data></left></right></node>'
        doc = pyxb.utils.domutils.StringToDOM(xml)
        instance = node.createFromDOM(doc.documentElement)
        self.assertEqual('root', instance.data)
        self.assertEqual('left1', instance.left.data)
        self.assertEqual('left2', instance.left.left.data)
        self.assertEqual('leftright', instance.left.right.data)
        self.assertEqual('right1', instance.right.data)
        self.assertEqual('rightleft', instance.right.left.data)

        instance = node('root', node('left1', node('left2'), node('leftright')), node('right1', node('rightleft')))
        self.assertEqual('root', instance.data)
        self.assertEqual('left1', instance.left.data)
        self.assertEqual('left2', instance.left.left.data)
        self.assertEqual('leftright', instance.left.right.data)
        self.assertEqual('right1', instance.right.data)
        self.assertEqual('rightleft', instance.right.left.data)

if __name__ == '__main__':
    unittest.main()
