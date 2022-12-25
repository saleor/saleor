# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import unittest
import pyxb

class TestTrac0199 (unittest.TestCase):

    def setUp (self):
        self.__pyxb_version = pyxb.__version__
        pyxb.__version__ = 'NOT ' + self.__pyxb_version

    def tearDown (self):
        pyxb.__version__ = self.__pyxb_version

    def testImport (self):
        try:
            import X
            self.assertFalse('exception not raised')
        except pyxb.PyXBVersionError as e:
            self.assertEqual(e.args[0], self.__pyxb_version)

if __name__ == '__main__':
    unittest.main()
