# -*- coding: iso-2022-jp -*-
from __future__ import unicode_literals
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
#

import sys
import pyxb.binding.generate
import pyxb.binding.datatypes as xs
import pyxb.binding.basis
import pyxb.utils.saxutils
from pyxb.utils import six
import tempfile
import xml.sax

import os.path
xsd='''<?xml version="1.0" encoding="utf-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
        <xs:element name="text" type="xs:string"/>
</xs:schema>
'''

#open('schema.xsd', 'w').write(xsd)
code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)
#print code

rv = compile(code.encode('utf-8'), 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac_0139 (unittest.TestCase):
    ascii_enc = sys.getdefaultencoding()
    asciit = 'something'
    nihongo_enc = 'iso-2022-jp'
    nihongot = '基盤地図情報ダウンロードデータ（GML版）'

    def buildDocument (self, text, encoding):
        map = { 'text' : text }
        if encoding is None:
            map['encoding'] = ''
        else:
            map['encoding'] = ' encoding="%s"' % (encoding,)
        return '<?xml version="1.0"%(encoding)s?><text>%(text)s</text>' % map

    # NOTE: Init-lower version does not exist before Python 2.7, so
    # make this non-standard and invoke it in init
    def SetUpClass (self):
        self.nihongo_xmlt = self.buildDocument(self.nihongot, self.nihongo_enc)
        (fd, self.path_nihongo) = tempfile.mkstemp()
        self.nihongo_xmld = self.nihongo_xmlt.encode(self.nihongo_enc)
        os.fdopen(fd, 'wb').write(self.nihongo_xmld)
        self.ascii_xmlt = self.buildDocument(self.asciit, self.ascii_enc)
        (fd, self.path_ascii) = tempfile.mkstemp()
        self.ascii_xmld = self.ascii_xmlt.encode(self.ascii_enc)
        os.fdopen(fd, 'wb').write(self.ascii_xmld)

        # Ensure test failures are not due to absence of libxml2,
        # which PyXB can't control.
        self.have_libxml2 = True
        try:
            import drv_libxml2
        except ImportError:
            self.have_libxml2 = False

    # NOTE: Init-lower version does not exist before Python 2.7, so
    # make this non-standard and invoke it in del
    def TearDownClass (self):
        os.remove(self.path_ascii)
        os.remove(self.path_nihongo)

    def useLibXML2Parser (self):
        pyxb.utils.saxutils.SetCreateParserModules(['drv_libxml2'])

    def tearDown (self):
        pyxb.utils.saxutils.SetCreateParserModules(None)

    def __init__ (self, *args, **kw):
        self.SetUpClass()
        super(TestTrac_0139, self).__init__(*args, **kw)

    def __del__ (self, *args, **kw):
        self.TearDownClass()
        try:
            super(TestTrac_0139, self).__del__(*args, **kw)
        except AttributeError:
            pass

    # Make sure create parser modules is reset after each test
    def tearDown (self):
        pyxb.utils.saxutils.SetCreateParserModules(None)

    def testParserTypes (self):
        import sys
        if sys.version_info < (3, 0):
            default_enc = 'ascii'
        else:
            default_enc = 'utf-8'
        self.assertEqual(default_enc, sys.getdefaultencoding())
        parser = pyxb.utils.saxutils.make_parser()
        self.assertTrue(isinstance(parser, xml.sax.expatreader.ExpatParser))
        if self.have_libxml2:
            import drv_libxml2
            self.useLibXML2Parser()
            parser = pyxb.utils.saxutils.make_parser()
            self.assertTrue(isinstance(parser, drv_libxml2.LibXml2Reader))

    def testASCII_expat_text (self):
        instance = CreateFromDocument(self.ascii_xmlt)
        self.assertEqual(self.asciit, instance)

    def testASCII_expat_data (self):
        instance = CreateFromDocument(self.ascii_xmld)
        self.assertEqual(self.asciit, instance)

    def testASCII_libxml2_str (self):
        if not self.have_libxml2:
            _log.warning('%s: testASCII_libxml2_str bypassed since libxml2 not present', __file__)
            return
        self.useLibXML2Parser()
        instance = CreateFromDocument(self.ascii_xmld)
        self.assertEqual(self.asciit, instance)

    def testASCII_expat_file (self):
        xmld = open(self.path_ascii, 'rb').read()
        instance = CreateFromDocument(xmld)
        self.assertEqual(self.asciit, instance)

    def testASCII_libxml2_file (self):
        if not self.have_libxml2:
            _log.warning('%s: testASCII_libxml2_file bypassed since libxml2 not present', __file__)
            return
        self.useLibXML2Parser()
        xmld = open(self.path_ascii, 'rb').read()
        instance = CreateFromDocument(xmld)
        self.assertEqual(self.asciit, instance)

    def testNihongo_expat_text (self):
        self.assertRaises(xml.sax.SAXParseException, CreateFromDocument, self.nihongo_xmlt)

    def testNihongo_expat_data (self):
        self.assertRaises(xml.sax.SAXParseException, CreateFromDocument, self.nihongo_xmld)

    def testNihongo_expat_file (self):
        xmld = open(self.path_nihongo, 'rb').read()
        self.assertRaises(xml.sax.SAXParseException, CreateFromDocument, xmld)

    def testNihongo_libxml2_str (self):
        if not self.have_libxml2:
            _log.warning('%s: testNihongo_libxml2_str bypassed since libxml2 not present', __file__)
            return
        self.assertRaises(xml.sax.SAXParseException, CreateFromDocument, self.nihongo_xmlt)
        # ERROR: This should be fine, see trac/147
        #instance = CreateFromDocument(self.nihongo_xmld)
        #self.assertEqual(self.nihongot, instance)
        self.assertRaises(xml.sax.SAXParseException, CreateFromDocument, self.nihongo_xmld)

    def testNihongo_libxml2_file (self):
        if not self.have_libxml2:
            _log.warning('%s: testNihongo_libxml2_file bypassed since libxml2 not present', __file__)
            return
        self.useLibXML2Parser()
        xmld = open(self.path_nihongo, 'rb').read()
        instance = CreateFromDocument(xmld)
        self.assertEqual(self.nihongot, instance)

    def testASCII_textio (self):
        f = open(self.path_ascii).read()
        sio = io.StringIO(self.ascii_xmlt).read()
        self.assertEqual(f, sio)

    def testASCII_dataio (self):
        f = open(self.path_ascii, 'rb').read()
        sio = io.BytesIO(self.ascii_xmld).read()
        self.assertEqual(f, sio)

if __name__ == '__main__':
    unittest.main()
