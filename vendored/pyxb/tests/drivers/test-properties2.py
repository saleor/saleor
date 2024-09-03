# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb
import pyxb.binding.generate
import pyxb.utils.domutils
from pyxb.utils import six
from xml.dom import Node

import pyxb.binding.basis
import os.path
schema_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../schemas/test-collision.xsd'))
code = pyxb.binding.generate.GeneratePython(schema_location=schema_path)
#open('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.utils import domutils

import unittest

class TestCollision (unittest.TestCase):

    def testBasic (self):
        instance = color(color_.red, color_=color_.green)
        xmlt = six.u('<color color="green"><color>red</color></color>')
        xmld = xmlt.encode('utf-8')
        self.assertEqual(instance.toxml("utf-8", root_only=True), xmld)
        instance.color = color_.blue
        xmlt = six.u('<color color="green"><color>blue</color></color>')
        xmld = xmlt.encode('utf-8')
        self.assertEqual(instance.toxml("utf-8", root_only=True), xmld)
        instance.color_ = color_.red
        xmlt = six.u('<color color="red"><color>blue</color></color>')
        xmld = xmlt.encode('utf-8')
        self.assertEqual(instance.toxml("utf-8", root_only=True), xmld)

if __name__ == '__main__':
    unittest.main()
