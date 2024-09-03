# -*- coding: utf-8 -*-

# Check all exceptions under pyxb.BindingError

import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)

import pyxb
import pyxb.binding.datatypes as xs
import trac26
import unittest
import sys

# By default skip the "tests" which actually emit the exception
# backtrace.  Sometimes though it's good to see those, since they're
# what the user will normally see first.
DisplayException = False
#DisplayException = True

class TestReservedNameError (unittest.TestCase):
    def testSchemaSupport (self):
        instance = trac26.eCTwSC(4)
        instance.nottoxml = 1

    def testException (self):
        instance = trac26.eCTwSC(4)
        with self.assertRaises(pyxb.ReservedNameError) as cm:
            instance.toxml = 1
        e = cm.exception
        self.assertEqual(e.instance, instance)
        self.assertEqual(e.name, 'toxml')

    def testDisplayException (self):
        if DisplayException:
            trac26.eCTwSC(4).toxml = 1

class TestNotComplexContentError (unittest.TestCase):
    # No tests on documents as the exception is raised only in code
    # that invokes the content() method.

    def testSchemaSupport (self):
        instance = trac26.eEmpty()
        instance = trac26.eCTwSC(4)

    def testEmptyException (self):
        content = None
        instance = trac26.eEmpty()
        with self.assertRaises(pyxb.NotComplexContentError) as cm:
            content = instance.orderedContent()
        e = cm.exception
        self.assertEqual(e.instance, instance)

    def testSimpleException (self):
        content = None
        instance = trac26.eCTwSC(4)
        with self.assertRaises(pyxb.NotComplexContentError) as cm:
            content = instance.orderedContent()
        e = cm.exception
        self.assertEqual(e.instance, instance)

    def testDisplayException (self):
        if DisplayException:
            trac26.eEmpty().orderedContent()

class TestNotSimpleContentError (unittest.TestCase):
    # No tests on documents as the exception is raised only in code
    # that invokes the content() method.

    def testSchemaSupport (self):
        instance = trac26.eEmpty()
        cym1 = trac26.tConcSubCymru('un')
        instance = trac26.eUseAbstract(cym1)

    def testEmptyException (self):
        value = None
        instance = trac26.eEmpty()
        with self.assertRaises(pyxb.NotSimpleContentError) as cm:
            value = instance.value()
        e = cm.exception
        self.assertEqual(e.instance, instance)

    def testComplexException (self):
        value = None
        instance = trac26.eUseAbstract(trac26.tConcSubCymru('un'))
        with self.assertRaises(pyxb.NotSimpleContentError) as cm:
            value = instance.value()
        e = cm.exception
        self.assertEqual(e.instance, instance)

    def testDisplayException (self):
        if DisplayException:
            trac26.eEmpty().value()

if __name__ == '__main__':
    if sys.version_info[:2] >= (2, 7):
        unittest.main()
    else:
        _log.warning('Cannot run test prior to Python 2.7')
