# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
from pyxb.utils.domutils import BindingDOMSupport
from pyxb.utils import six
import unittest

import bindings._A as A

class Test (unittest.TestCase):
    def setUp (self):
        BindingDOMSupport.DeclareNamespace(A.Namespace, 'a')

    def tearDown (self):
        BindingDOMSupport.Reset()

    def tests (self):
        x = A.A_c_e1("A_b_e1", "e1")
        xmlt = six.u('<a:A_c_e1 xmlns:a="URN:nsdep:A"><a:A_b_e1>A_b_e1</a:A_b_e1><a:e1>e1</a:e1></a:A_c_e1>')
        xmld = xmlt.encode('utf-8')
        self.assertEqual(x.toxml("utf-8", root_only=True), xmld)

if '__main__' == __name__:
    unittest.main()
