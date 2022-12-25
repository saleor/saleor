# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import unittest
import app
import common

import pyxb.utils.domutils
from pyxb.utils import six

pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(app.Namespace, 'app')
pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(common.Namespace, 'common')

class Test (unittest.TestCase):

    def testMissingApp (self):
        # The app element is not in the base common, it's in the
        # application-specific module that's private.
        self.assertRaises(AttributeError, getattr, common, 'app')

    def testApp (self):
        instance = app.elt(base='hi', app='there')
        xmlt = six.u('<app:elt xmlns:app="urn:app" xmlns:common="urn:common"><common:base><common:bstr>hi</common:bstr></common:base><common:app><common:astr>there</common:astr></common:app></app:elt>')
        xmld = xmlt.encode('utf-8')
        self.assertEqual(instance.toxml('utf-8', root_only=True), xmld)

if '__main__' == __name__:
    unittest.main()
