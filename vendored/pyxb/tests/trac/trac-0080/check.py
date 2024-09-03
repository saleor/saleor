# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import mr
import unittest
import pyxb
import pyxb.binding.datatypes as xsd

class TestTrac0080 (unittest.TestCase):

    _NotANormalizedString = "\nmulti\nline\ttabbed\n"
    _NotAToken = ' leading spaces '
    _NotAnNCName = 'internal spaces'
    _NCName = 'simple'

    def assignAttribute_ (self, instance, value):
        instance.anAttribute = value

    def testType4 (self): # base
        i4 = mr.Type4()
        au = i4._AttributeMap.get('anAttribute')
        self.assertEqual(au.dataType(), xsd.normalizedString)
        self.assertFalse(au.required())
        self.assertRaises(pyxb.SimpleTypeValueError, self.assignAttribute_, i4, self._NotANormalizedString)

    def testType3 (self): # restrict type
        i3 = mr.Type3()
        au = i3._AttributeMap.get('anAttribute')
        self.assertEqual(au.dataType(), xsd.token)
        self.assertNotEqual(au, mr.Type4._AttributeMap.get(au.name()))
        self.assertFalse(au.required())
        #self.assertRaises(pyxb.SimpleTypeValueError, self.assignAttribute_, i3, self._NotAToken)
        self.assignAttribute_(i3, self._NotAnNCName)
        self.assertEqual(self._NotAnNCName, i3.anAttribute)

    def testType2 (self): # extend isSet
        i2 = mr.Type2()
        au = i2._AttributeMap.get('anAttribute')
        self.assertEqual(au.dataType(), xsd.token)
        self.assertEqual(au, mr.Type3._AttributeMap.get(au.name()))
        self.assertFalse(au.required())

    def testType1 (self): # restrict type
        i1 = mr.Type1()
        au = i1._AttributeMap.get('anAttribute')
        self.assertEqual(au.dataType(), xsd.NCName)
        self.assertFalse(au.required())
        # The whiteSpace facet on xsd:token is collapse, which does
        # not remove the interior space.
        self.assertRaises(pyxb.SimpleTypeValueError, self.assignAttribute_, i1, self._NotAToken)
        self.assertRaises(pyxb.SimpleTypeValueError, self.assignAttribute_, i1, self._NotAnNCName)
        self.assignAttribute_(i1, self._NCName)
        self.assertEqual(self._NCName, i1.anAttribute)

    def testRoot (self): # restrict required
        r = mr.root()
        rt = type(r)
        au = rt._AttributeMap.get('anAttribute')
        self.assertEqual(au.dataType(), xsd.NCName)
        self.assertTrue(au.required())
        self.assertRaises(pyxb.MissingAttributeError, r.validateBinding)

if __name__ == '__main__':
    unittest.main()
