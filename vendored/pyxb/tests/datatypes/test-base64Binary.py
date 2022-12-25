# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import unittest
import binascii
import pyxb
import pyxb.binding.datatypes as xsd
from pyxb.utils import six

class Test_base64Binary (unittest.TestCase):
    RFC4648_S9 = ( (six.u('14fb9c03d97e'), six.u('FPucA9l+')),
                   (six.u('14fb9c03d9'), six.u('FPucA9k=')),
                   (six.u('14fb9c03'), six.u('FPucAw==')) )
    RFC4648_S10 = ( (six.u(''), six.u('')),
                    (six.u('f'), six.u('Zg==')),
                    (six.u('fo'), six.u('Zm8=')),
                    (six.u('foo'), six.u('Zm9v')),
                    (six.u('foob'), six.u('Zm9vYg==')),
                    (six.u('fooba'), six.u('Zm9vYmE=')),
                    (six.u('foobar'), six.u('Zm9vYmFy')) )
    def testVectors (self):
        """RFC4648 section 10."""
        for (plaintext, ciphertext) in self.RFC4648_S10:
            plaintexd = plaintext.encode('utf-8')
            ciphertexd = ciphertext.encode('utf-8')
            self.assertEqual(xsd.base64Binary(plaintexd).xsdLiteral(), ciphertext)
            self.assertEqual(xsd.base64Binary(ciphertext, _from_xml=True), plaintexd)
        for (hextext, ciphertext) in self.RFC4648_S9:
            hextexd = hextext.encode('utf-8')
            plaintexd = binascii.unhexlify(hextexd)
            self.assertEqual(xsd.base64Binary(plaintexd).xsdLiteral(), ciphertext)
            self.assertEqual(xsd.base64Binary(ciphertext, _from_xml=True), plaintexd)

    def tearDown (self):
        xsd.base64Binary.XsdValidateLength(None)

    def testLimitValidation (self):
        self.assertRaises(TypeError, xsd.base64Binary.XsdValidateLength, 'hi')

    def testLimitOverride (self):
        self.assertEqual(six.b('e'), xsd.base64Binary(six.u('ZQ=='), _from_xml=True))
        self.assertEqual(six.b('e\x96'), xsd.base64Binary(six.u('ZZY='), _from_xml=True))
        self.assertRaises(pyxb.SimpleTypeValueError, xsd.base64Binary, six.u('ZZZ='), _from_xml=True)
        xsd.base64Binary.XsdValidateLength(-1)
        self.assertEqual(six.b('e\x96'), xsd.base64Binary(six.u('ZZZ='), _from_xml=True))
        xsd.base64Binary.XsdValidateLength(3)
        self.assertEqual(six.b('e\x96'), xsd.base64Binary(six.u('ZZZ='), _from_xml=True))
        xsd.base64Binary.XsdValidateLength(4)
        self.assertRaises(pyxb.SimpleTypeValueError, xsd.base64Binary, six.u('ZZZ='), _from_xml=True)

    def testInvalid (self):
        self.assertRaises(pyxb.SimpleTypeValueError, xsd.base64Binary, six.u('Z'), _from_xml=True)
        self.assertRaises(pyxb.SimpleTypeValueError, xsd.base64Binary, six.u('Zg'), _from_xml=True)
        self.assertRaises(pyxb.SimpleTypeValueError, xsd.base64Binary, six.u('Zg='), _from_xml=True)
        self.assertEqual(six.u('f').encode('utf-8'), xsd.base64Binary(six.u('Zg=='), _from_xml=True))
        self.assertRaises(pyxb.SimpleTypeValueError, xsd.base64Binary, six.u('ZZZ='), _from_xml=True)
        self.assertRaises(pyxb.SimpleTypeValueError, xsd.base64Binary, six.u('ZZ=='), _from_xml=True)
        self.assertRaises(pyxb.SimpleTypeValueError, xsd.base64Binary, six.u('ZE=='), _from_xml=True)

if __name__ == '__main__':
    unittest.main()
