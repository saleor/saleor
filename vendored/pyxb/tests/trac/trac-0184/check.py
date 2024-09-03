# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.utils.domutils
from pyxb.utils import six

import bindings.s0 as s0
import bindings.s1 as s1

pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(s0.Namespace, 's0')
pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(s1.Namespace, 's1')

import unittest

class ExternalTrac0184 (unittest.TestCase):
    def testExtend0 (self):
        e0i = s0.e0i(32)
        e1i = s1.e1i(4)
        e1s = s1.e1s('ext0')
        e0extend0 = s0.e0extend0()
        self.assertRaises(pyxb.IncompleteElementContentError, e0extend0.toxml, 'utf-8')
        e0extend0.e0i = e0i
        xmlt = six.u('<s0:e0extend0 xmlns:s0="urn:s0add"><s0:e0i>32</s0:e0i></s0:e0extend0>')
        xmld = xmlt.encode('utf-8')
        self.assertEqual(e0extend0.toxml('utf-8', root_only=True), xmld)
        e0extend0.e1i = e1i
        xmlt = six.u('<s0:e0extend0 xmlns:s0="urn:s0add" xmlns:s1="urn:s1core"><s1:e1i>4</s1:e1i><s0:e0i>32</s0:e0i></s0:e0extend0>')
        xmld = xmlt.encode('utf-8')
        self.assertEqual(e0extend0.toxml('utf-8', root_only=True), xmld)
        e0extend0.e1s = e1s
        xmlt = six.u('<s0:e0extend0 xmlns:s0="urn:s0add" xmlns:s1="urn:s1core"><s1:e1i>4</s1:e1i><s1:e1s>ext0</s1:e1s><s0:e0i>32</s0:e0i></s0:e0extend0>')
        xmld = xmlt.encode('utf-8')
        self.assertEqual(e0extend0.toxml('utf-8', root_only=True), xmld)

    def testExtend1 (self):
        e0i = s0.e0i(32)
        e1i = s1.e1i(4)
        e1s = s1.e1s('ext1')
        e0extend1 = s0.e0extend1()
        self.assertRaises(pyxb.IncompleteElementContentError, e0extend1.toxml, 'utf-8')
        e0extend1.e0i = e0i
        xmlt = six.u('<s0:e0extend1 xmlns:s0="urn:s0add"><s0:e0i>32</s0:e0i></s0:e0extend1>')
        xmld = xmlt.encode('utf-8')
        self.assertEqual(e0extend1.toxml('utf-8', root_only=True), xmld)
        e0extend1.e1i = e1i
        xmlt = six.u('<s0:e0extend1 xmlns:s0="urn:s0add" xmlns:s1="urn:s1core"><s1:e1i>4</s1:e1i><s0:e0i>32</s0:e0i></s0:e0extend1>')
        xmld = xmlt.encode('utf-8')
        self.assertEqual(e0extend1.toxml('utf-8', root_only=True), xmld)
        e0extend1.e1s = e1s
        xmlt = six.u('<s0:e0extend1 xmlns:s0="urn:s0add" xmlns:s1="urn:s1core"><s1:e1s>ext1</s1:e1s><s1:e1i>4</s1:e1i><s0:e0i>32</s0:e0i></s0:e0extend1>')
        xmld = xmlt.encode('utf-8')
        self.assertEqual(e0extend1.toxml('utf-8', root_only=True), xmld)

if '__main__' == __name__:
    unittest.main()
