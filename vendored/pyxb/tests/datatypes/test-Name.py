# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
from pyxb.exceptions_ import *
import unittest
import pyxb.binding.datatypes as xsd

class Test_Name (unittest.TestCase):
    def testValid (self):
        valid = [ 'schema', '_Underscore', '_With.Dot', 'With-Hyphen',
                  'With:Colon' ]
        for f in valid:
            self.assertEqual(f, xsd.Name(f))

    def testInvalid (self):
        invalid = [ '.DotFirst', 'With Spaces',
                    'With?Illegal', '??LeadingIllegal', 'TrailingIllegal??',
                    '  LeadingSpace', 'TrailingSpace   ']
        for f in invalid:
            self.assertRaises(SimpleTypeValueError, xsd.Name, f)

if __name__ == '__main__':
    unittest.main()
