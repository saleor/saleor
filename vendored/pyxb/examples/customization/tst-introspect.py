import pyxb
import introspect as custom
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

    def testCustomSubclassesRaw (self):
        self.assertTrue(issubclass(custom.tc01, raw_custom.tc01))
        self.assertTrue(issubclass(custom.tc02, raw_custom.tc02))
        self.assertTrue(issubclass(custom.tc03, raw_custom.tc03))
        self.assertTrue(issubclass(custom.ta04, raw_custom.ta04))
        self.assertTrue(issubclass(custom.tc041, raw_custom.tc041))
        self.assertTrue(issubclass(custom.tc042, raw_custom.tc042))

    def testCustomConcreteHierarchy (self):
        self.assertTrue(issubclass(custom.tc041, custom.ta04))
        self.assertTrue(issubclass(custom.tc042, custom.ta04))

    def testSupersedureReplacement (self):
        self.assertEqual(custom.ta0, raw_custom.ta0)
        self.assertEqual(custom.tc01, raw_custom.tc01)
        self.assertEqual(custom.tc02, raw_custom.tc02)
        self.assertEqual(custom.tc03, raw_custom.tc03)
        self.assertNotEqual(custom.ta04, raw_custom.ta04)
        self.assertNotEqual(custom.tc041, raw_custom.tc041)
        self.assertNotEqual(custom.tc042, raw_custom.tc042)

    def test_c041 (self):
        ec041 = self.instance.ec041
        self.assertTrue(isinstance(ec041, custom.tc041))
        self.assertEqual(ec041.ea0, 'ec041')
        self.assertEqual(ec041.ea04_s, 'a04')
        self.assertEqual(ec041.ec041_s, 'c041')
        self.assertEqual(ec041.xa04(), 'extend ta04')

    def test_c042 (self):
        ec042 = self.instance.ec042
        self.assertTrue(isinstance(ec042, custom.tc042))
        self.assertEqual(ec042.ea0, 'ec042')
        self.assertEqual(ec042.ea04_s, 'a04')
        self.assertEqual(ec042.ec042_i, 42)
        self.assertEqual(ec042.xa04(), 'extend ta04')


if __name__ == '__main__':
    unittest.main()

