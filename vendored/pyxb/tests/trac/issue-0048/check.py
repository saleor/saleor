# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import profile
import unittest

class TestIssue0048 (unittest.TestCase):
    def testProfile (self):
        amap = profile.AbstractFeatureBaseType._AttributeMap
        self.assertEqual(1, len(amap))

if __name__ == '__main__':
    unittest.main()
