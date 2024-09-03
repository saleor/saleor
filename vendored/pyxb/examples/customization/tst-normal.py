import pyxb
import normal as custom
import raw.custom as raw_custom

import unittest

class TestComplex (unittest.TestCase):

    def setUp (self):
        xmls = open('test.xml').read()
        self.instance = custom.CreateFromDocument(xmls)

    def testRawSubclassHierarchy (self):
        self.assertTrue(issubclass(raw_custom.tc01, raw_custom.ta0))
        self.assertTrue(issubclass(raw_custom.tc02, raw_custom.ta0))
        self.assertTrue(issubclass(raw_custom.tc03, raw_custom.ta0))
        self.assertTrue(issubclass(raw_custom.ta04, raw_custom.ta0))
        self.assertTrue(issubclass(raw_custom.tc041, raw_custom.ta04))
        self.assertTrue(issubclass(raw_custom.tc042, raw_custom.ta04))

    def testCustomSubclassesRaw(self):
        self.assertTrue(issubclass(custom.tc01, raw_custom.tc01))
        self.assertTrue(issubclass(custom.tc02, raw_custom.tc02))
        self.assertTrue(issubclass(custom.tc03, raw_custom.tc03))
        self.assertTrue(issubclass(custom.ta04, raw_custom.ta04))
        self.assertTrue(issubclass(custom.tc041, raw_custom.tc041))
        self.assertTrue(issubclass(custom.tc042, raw_custom.tc042))

    def testCustomConcreteHierarchy(self):
        self.assertFalse(issubclass(custom.tc01, custom.ta0))
        self.assertTrue(issubclass(custom.tc02, custom.ta0))
        self.assertFalse(issubclass(custom.tc03, custom.ta0))

    def test_c01 (self):
        ec01 = self.instance.ec01
        self.assertTrue(isinstance(ec01, custom.tc01))
        self.assertEqual(ec01.ea0, 'ec01')
        self.assertEqual(ec01.ec01, 'c01')
        # Direct customization works...
        self.assertEqual(ec01.xc01(), 'extend tc01')
        # No inheritance from customized superclass
        self.assertRaises(AttributeError, lambda _i: _i.xa0, ec01)

    def test_c02 (self):
        # Dual-inheritance customization works
        ec02 = self.instance.ec02
        self.assertTrue(isinstance(ec02, custom.tc02))
        self.assertEqual(ec02.ea0, 'ec02')
        self.assertEqual(ec02.ec02_i, 2)
        # Direct customization works
        self.assertEqual(ec02.xc02(), 'extend tc02')
        # Inherited customization works
        self.assertEqual(ec02.xa0(), 'extend ta0')

    def test_c03 (self):
        ec03 = self.instance.ec03
        self.assertTrue(isinstance(ec03, custom.tc03))
        self.assertEqual(ec03.ea0, 'ec03')
        self.assertTrue(ec03.ec03_b)
        # No inheritance from customized superclass
        self.assertRaises(AttributeError, lambda _i: _i.xa0, ec03)

if __name__ == '__main__':
    unittest.main()

