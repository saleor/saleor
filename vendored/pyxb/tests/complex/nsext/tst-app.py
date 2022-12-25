# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import unittest
import app
import common4app

import pyxb.utils.domutils
from pyxb.utils import six

pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(app.Namespace, 'app')
pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(common4app.Namespace, 'common')

class Test (unittest.TestCase):
    def testApp (self):
        x = common4app.extended('hi', 'there')
        a = app.elt(x)
        xmlt = six.u('<app:elt xmlns:app="urn:app" xmlns:common="urn:common"><app:xcommon><common:elt>hi</common:elt><common:extElt>there</common:extElt></app:xcommon></app:elt>')
        xmld = xmlt.encode('utf-8')
        self.assertEqual(a.toxml("utf-8", root_only=True), xmld)

if '__main__' == __name__:
    unittest.main()
