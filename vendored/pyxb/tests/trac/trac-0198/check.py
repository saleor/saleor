# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import unittest

import wsse
import wsu

from pyxb.utils.domutils import BindingDOMSupport
from pyxb.utils import six

BindingDOMSupport.DeclareNamespace(wsu.Namespace, 'wsu')
BindingDOMSupport.DeclareNamespace(wsse.Namespace, 'wsse')

class TestTrac0198 (unittest.TestCase):
    def testFindWsu (self):
        self.assertEqual(3, len(wsse.tAttributedString._AttributeMap))
        for (n, ad) in six.iteritems(wsse.tAttributedString._AttributeMap):
            if (n.localName() == "agu"):
                self.assertEqual(None, n.namespace())
            else:
                self.assertEqual(wsu.Namespace, n.namespace())
        self.assertEqual(2, len(wsse.tComplexElt._ElementMap))
        for (n, ad) in six.iteritems(wsse.tComplexElt._ElementMap):
            if n.localName() == 'Elt':
                self.assertEqual(wsu.Namespace, n.namespace())
            elif n.localName() == 'local':
                self.assertEqual(None, n.namespace())
            else:
                self.assertFalse()

if __name__ == '__main__':
    unittest.main()
