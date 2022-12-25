# -*- coding: utf-8 -*-

# Check all exceptions under pyxb.ValidationError

# ElementValidationError
# . AbstractElementError
# . ContentInNilInstanceError
# . NoNillableSupportError
# ComplexTypeValidationError
# . AbstractInstantiationError
# . AttributeOnSimpleTypeError
# . ContentValidationError
# - - BatchElementContentError
# - - + IncompleteElementContentError
# - - + UnprocessedElementContentError
# - - IncrementalElementContentError
# - - + UnrecognizedContentError
# - + ExtraSimpleContentError
# - + MixedContentError
# - + SimpleContentAbsentError
# - + UnprocessedKeywordContentError
# AttributeValidationError
# . AttributeChangeError
# . MissingAttributeError
# . ProhibitedAttributeError
# . UnrecognizedAttributeError
# SimpleTypeValueError
# * SimpleFacetValueError
# . SimpleListValueError
# * SimplePluralValueError
# * SimpleUnionValueError

import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)

import pyxb
import pyxb.binding.datatypes as xs
from pyxb.utils import six
import trac26
import unittest
import sys
import xml.dom

# By default skip the "tests" which actually emit the exception
# backtrace.  Sometimes though it's good to see those, since they're
# what the user will normally see first.  Also, this is how we ensure
# that each point where a particular exception might be raised has a
# test case covering it.
DisplayException = False
#DisplayException = True

class TestAbstractElementError (unittest.TestCase):
    Good_xmlt = six.u('<eCardinals><eConcCardCymru>un</eConcCardCymru><eConcCardEnglish>three</eConcCardEnglish></eCardinals>')
    Good_xmld = Good_xmlt.encode('utf-8')

    Bad_xmlt = six.u('<eCardinals><eConcCardCymru>un</eConcCardCymru><eAbstractCard>three</eAbstractCard></eCardinals>')
    Bad_xmld = Bad_xmlt.encode('utf-8')

    def testSchemaSupport (self):
        cym1 = trac26.eConcCardCymru('un')
        eng3 = trac26.eConcCardEnglish('three')

        # Incremental through owning element
        instance = trac26.eCardinals()
        self.assertEqual(0, len(instance.eAbstractCard))
        instance.append(cym1)
        self.assertEqual(1, len(instance.eAbstractCard))
        self.assertTrue(isinstance(instance.eAbstractCard[0], trac26.tCardCymru))
        instance.append(eng3)
        self.assertEqual(2, len(instance.eAbstractCard))
        self.assertTrue(isinstance(instance.eAbstractCard[1], trac26.tCardEnglish))
        self.assertTrue(instance.validateBinding())
        xmld = instance.toxml('utf-8', root_only=True)
        self.assertEqual(xmld, self.Good_xmld)

        # Incremental through construtor element
        instance = trac26.eCardinals(cym1, eng3)
        self.assertEqual(2, len(instance.eAbstractCard))
        self.assertTrue(isinstance(instance.eAbstractCard[0], trac26.tCardCymru))
        self.assertTrue(isinstance(instance.eAbstractCard[1], trac26.tCardEnglish))
        self.assertTrue(instance.validateBinding())
        xmld = instance.toxml('utf-8', root_only=True)
        self.assertEqual(xmld, self.Good_xmld)

        # Through parsing
        instance = trac26.CreateFromDocument(self.Good_xmlt)
        self.assertEqual(2, len(instance.eAbstractCard))
        self.assertTrue(isinstance(instance.eAbstractCard[0], trac26.tCardCymru))
        self.assertTrue(isinstance(instance.eAbstractCard[1], trac26.tCardEnglish))
        self.assertTrue(instance.validateBinding())

    def testException (self):
        instance = None
        with self.assertRaises(pyxb.AbstractElementError) as cm:
            instance = trac26.eAbstractCard('un')
        e = cm.exception
        self.assertTrue(instance is None)
        self.assertEqual(e.element, trac26.eAbstractCard)
        self.assertEqual(e.value, ('un',))
        self.assertEqual(str(e), 'Cannot instantiate abstract element eAbstractCard directly')

    def testFromDocument (self):
        instance = None
        with self.assertRaises(pyxb.AbstractElementError) as cm:
            instance = trac26.CreateFromDocument(self.Bad_xmlt)
        e = cm.exception
        self.assertFalse((e.location is None) and (pyxb.XMLStyle_saxer == pyxb._XMLStyle))
        if e.location is not None:
            self.assertEqual(1, e.location.lineNumber)
            self.assertEqual(47, e.location.columnNumber)

    def testDisplayException (self):
        if DisplayException:
            trac26.eAbstractCard('un')

    def testIncremental (self):
        # Without type information, incremental does not work.  The content
        # model fails to recognize it, and it looks like mixed content.
        instance = trac26.eCardinals()
        self.assertEqual(0, len(instance.eAbstractCard))
        self.assertRaises(pyxb.MixedContentError, instance.append, 'un')

class TestAbstractInstantiationError (unittest.TestCase):

    Good_xmlt = six.u('<eUseAbstract xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><eAbstract xsi:type="tConcSubCymru"><welsh>un</welsh></eAbstract></eUseAbstract>')
    Good_xmld = Good_xmlt.encode('utf-8')

    Bad_xmlt = six.u('<eUseAbstract xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><eAbstract><welsh>un</welsh></eAbstract></eUseAbstract>')
    Bad_xmld = Bad_xmlt.encode('utf-8')

    def testSchemaSupport (self):
        cym1 = trac26.tConcSubCymru('un')
        eng3 = trac26.tConcSubEnglish('three')
        # Direct generation works
        instance = trac26.eUseAbstract(cym1)
        # So does from documents with xsi:type
        i2 = trac26.CreateFromDocument(self.Good_xmlt)
        self.assertTrue(isinstance(i2.eAbstract, trac26.tConcSubCymru))

    def testException (self):
        scym1 = trac26.tCardCymru('un')
        instance = None
        with self.assertRaises(pyxb.AbstractInstantiationError) as cm:
            instance = trac26.eAbstract(scym1)
        e = cm.exception
        self.assertTrue(instance is None)
        self.assertEqual(str(e), 'Cannot instantiate abstract type tAbstract directly')

    def testFromDocument (self):
        instance = None
        with self.assertRaises(pyxb.AbstractInstantiationError) as cm:
            instance = trac26.CreateFromDocument(self.Bad_xmlt)
        e = cm.exception
        self.assertTrue(instance is None)
        # Location within Bad_xmlt where error occurred
        self.assertFalse((e.location is None) and (pyxb.XMLStyle_saxer == pyxb._XMLStyle))
        if e.location is not None:
            self.assertEqual(1, e.location.lineNumber)
            self.assertEqual(68, e.location.columnNumber)

    def testDisplayException (self):
        if DisplayException:
            scym1 = trac26.tCardCymru('un')
            trac26.eAbstract(scym1)

    def testDisplayExceptionDoc (self):
        if DisplayException:
            instance = trac26.CreateFromDocument(self.Bad_xmlt)

class TestSimpleContentAbsentError (unittest.TestCase):

    Good_xmlt = six.u('<eCTwSC>3</eCTwSC>')
    Good_xmld = Good_xmlt.encode('utf-8')
    Bad_xmlt = six.u('<eCTwSC></eCTwSC>')
    Bad_xmld = Bad_xmlt.encode('utf-8')

    GoodSeq_xmlt = six.u('<eCTwSCSequence><eCTwSC>1</eCTwSC><eCTwSC>2</eCTwSC></eCTwSCSequence>')
    GoodSeq_xmld = GoodSeq_xmlt.encode('utf-8')
    BadSeq_xmlt = six.u('<eCTwSCSequence><eCTwSC>1</eCTwSC><eCTwSC></eCTwSC></eCTwSCSequence>')
    BadSeq_xmld = BadSeq_xmlt.encode('utf-8')

    def testSchemaSupport (self):
        instance = trac26.eCTwSC(3)
        self.assertEqual(3, instance.value())
        instance = trac26.CreateFromDocument(self.Good_xmlt)
        self.assertEqual(3, instance.value())
        instance = trac26.eCTwSCSequence()
        # Can't infer conversion, see trac/175
        instance.eCTwSC.append(trac26.eCTwSC(1))
        instance.eCTwSC.append(trac26.eCTwSC(2))
        instance = trac26.CreateFromDocument(self.GoodSeq_xmlt)
        xmld = instance.toxml('utf-8', root_only=True)
        self.assertEqual(xmld, self.GoodSeq_xmld)

    def testDirect (self):
        instance = None
        with self.assertRaises(pyxb.SimpleContentAbsentError) as cm:
            instance = trac26.eCTwSC()
        e = cm.exception
        self.assertTrue(instance is None)

    def testXsdConstraints (self):
        instance = trac26.eCTwSC(3)
        self.assertTrue(instance.validateBinding())
        instance.reset()
        with self.assertRaises(pyxb.SimpleContentAbsentError) as cm:
            instance.xsdConstraintsOK()
        e = cm.exception
        self.assertEqual(str(e), 'Type tCTwSC requires content')

    def testAfterReset (self):
        instance = trac26.eCTwSC(3)
        self.assertTrue(instance.validateBinding())
        instance.reset()
        with self.assertRaises(pyxb.SimpleContentAbsentError) as cm:
            instance.validateBinding()
        e = cm.exception
        self.assertEqual(str(e), 'Type tCTwSC requires content')

    def testDocument (self):
        instance = None
        with self.assertRaises(pyxb.SimpleContentAbsentError) as cm:
            instance = trac26.CreateFromDocument(self.Bad_xmlt)
        e = cm.exception
        self.assertTrue(instance is None)
        self.assertFalse((e.location is None) and (pyxb.XMLStyle_saxer == pyxb._XMLStyle))
        if e.location is not None:
            self.assertEqual(1, e.location.lineNumber)
            self.assertEqual(0, e.location.columnNumber)
        self.assertEqual(str(e), 'Type {http://www.w3.org/2001/XMLSchema}int requires content')

    def testDocumentSeq (self):
        instance = None
        with self.assertRaises(pyxb.SimpleContentAbsentError) as cm:
            instance = trac26.CreateFromDocument(self.BadSeq_xmlt)
        e = cm.exception
        self.assertTrue(instance is None)
        self.assertFalse((e.location is None) and (pyxb.XMLStyle_saxer == pyxb._XMLStyle))
        if e.location is not None:
            self.assertEqual(1, e.location.lineNumber)
            self.assertEqual(34, e.location.columnNumber)
        self.assertEqual(str(e), 'Type {http://www.w3.org/2001/XMLSchema}int requires content')

    def testDisplayException (self):
        if DisplayException:
            instance = trac26.eCTwSC()

    def testDisplayExceptionDoc (self):
        if DisplayException:
            instance = trac26.CreateFromDocument(self.BadSeq_xmlt)

    def testDisplayExceptionReset (self):
        if DisplayException:
            instance = trac26.eCTwSC(3)
            instance.reset()
            instance.validateBinding()

    def testDisplayExceptionXsdConstraints (self):
        if DisplayException:
            instance = trac26.eCTwSC(3)
            instance.reset()
            instance.xsdConstraintsOK()

class TestAttributeChangeError (unittest.TestCase):

    Good_xmlt = six.u('<eAttributes aFixed="5" aReq="2"/>')
    Good_xmld = Good_xmlt.encode('utf-8')
    Bad_xmlt = six.u('<eAttributes aFixed="2" aReq="2"/>')
    Bad_xmld = Bad_xmlt.encode('utf-8')

    def testSchemaSupport (self):
        instance = trac26.tAttributes(aReq=2)
        self.assertEqual(instance.aReq, 2)
        self.assertEqual(instance.aFixed, 5)
        self.assertTrue(instance.validateBinding())
        # OK to explicitly assign fixed value
        instance.aFixed = 5
        instance = trac26.CreateFromDocument(self.Good_xmlt)
        self.assertEqual(self.Good_xmld, instance.toxml('utf-8',root_only=True))

    def testDirect (self):
        instance = trac26.tAttributes(aReq=2)
        with self.assertRaises(pyxb.AttributeChangeError) as cm:
            instance.aFixed = 1
        e = cm.exception
        self.assertEqual(e.type, trac26.tAttributes)
        self.assertEqual(e.tag, 'aFixed')
        self.assertEqual(e.instance, instance)
        self.assertTrue(e.location is None)

    def testDisplayException (self):
        if DisplayException:
            trac26.tAttributes(aReq=2).aFixed = 1

    def testDocument (self):
        instance = None
        with self.assertRaises(pyxb.AttributeChangeError) as cm:
            instance = trac26.CreateFromDocument(self.Bad_xmlt)
        self.assertTrue(instance is None)
        e = cm.exception
        self.assertEqual(e.type, trac26.tAttributes)
        self.assertEqual(e.tag, 'aFixed')
        self.assertFalse(e.instance is None) # there, but partially defined
        self.assertFalse((e.location is None) and (pyxb.XMLStyle_saxer == pyxb._XMLStyle))
        if e.location is not None:
            self.assertEqual(1, e.location.lineNumber)
            self.assertEqual(0, e.location.columnNumber)

    def testDisplayExceptionDoc (self):
        if DisplayException:
            trac26.CreateFromDocument(self.Bad_xmlt)

class TestAttributeValueError (unittest.TestCase):
    # AttributeValueError was intended to be raised when batch
    # validation discovered that the value was not suited for the type
    # of the attribute.  This can no longer happen since attribute
    # values are validated when they are assigned.  Consequently such
    # errors show up as SimpleTypeValueErrors.  Test for those instead.

    Good_xmlt = six.u('<eAttributes aCardCymru="pedwar" aReq="4"/>')
    Good_xmld = Good_xmlt.encode('utf-8')
    Bad_xmlt = six.u('<eAttributes aCardCymru="four" aReq="4"/>')
    Bad_xmld = Bad_xmlt.encode('utf-8')

    def testSchemaSupport (self):
        instance = trac26.tAttributes(aCardCymru='pedwar', aReq=4)
        self.assertTrue(instance.validateBinding())
        instance = trac26.CreateFromDocument(self.Good_xmlt)
        self.assertEqual(self.Good_xmld, instance.toxml('utf-8', root_only=True))
        instance.aCardCymru = 'dau'
        self.assertTrue(instance.validateBinding())

    def testAssignment (self):
        instance = trac26.eAttributes(aReq=4)
        with self.assertRaises(pyxb.SimpleTypeValueError) as cm:
            instance.aCardCymru = 'four'
        e = cm.exception
        au = trac26.tAttributes._AttributeMap['aCardCymru']
        self.assertTrue(isinstance(e, pyxb.SimpleFacetValueError))
        self.assertEqual(e.type, au.dataType())
        self.assertEqual(e.value, 'four')
        self.assertEqual(e.facet, au.dataType()._CF_enumeration)
        self.assertEqual(str(e), "Type tCardCymru enumeration constraint violated by value four")

    def testConstructor (self):
        with self.assertRaises(pyxb.SimpleTypeValueError) as cm:
            instance = trac26.eAttributes(aReq=4, aCardCymru='four')

    def testDocument (self):
        with self.assertRaises(pyxb.SimpleTypeValueError) as cm:
            instance = trac26.CreateFromDocument(self.Bad_xmlt)

class TestMissingAttributeError (unittest.TestCase):
    Good_xmlt = six.u('<eAttributes aReq="4"/>')
    Good_xmld = Good_xmlt.encode('utf-8')
    Bad_xmlt = six.u('<eAttributes/>')
    Bad_xmld = Bad_xmlt.encode('utf-8')

    def testSchemaSupport (self):
        instance = trac26.tAttributes(aReq=4)
        self.assertTrue(instance.validateBinding())
        instance = trac26.tAttributeReqFixed(aReqFixed=9)
        self.assertTrue(instance.validateBinding())
        instance = trac26.CreateFromDocument(self.Good_xmlt)
        self.assertEqual(self.Good_xmld, instance.toxml('utf-8', root_only=True))

    def testBatch (self):
        instance = trac26.tAttributes()
        with self.assertRaises(pyxb.MissingAttributeError) as cm:
            instance.validateBinding()

    def testBatchReqFixed (self):
        instance = trac26.tAttributeReqFixed()
        with self.assertRaises(pyxb.MissingAttributeError) as cm:
            instance.validateBinding()

    def testAssignment (self):
        instance = trac26.tAttributes(aReq=3)
        self.assertTrue(instance.validateBinding())
        with self.assertRaises(pyxb.MissingAttributeError) as cm:
            instance.aReq = None
        e = cm.exception
        self.assertEqual(e.instance, instance)

    def testDocument (self):
        instance = None
        with self.assertRaises(pyxb.MissingAttributeError) as cm:
            instance = trac26.CreateFromDocument(self.Bad_xmlt)
        e = cm.exception
        au = trac26.tAttributes._AttributeMap['aReq']
        self.assertFalse(e.instance is None)
        self.assertEqual(e.type, trac26.tAttributes)
        self.assertFalse((e.location is None) and (pyxb.XMLStyle_saxer == pyxb._XMLStyle))
        if e.location is not None:
            self.assertEqual(1, e.location.lineNumber)
            self.assertEqual(0, e.location.columnNumber)
        self.assertEqual(str(e), "Instance of <class 'trac26.tAttributes'> lacks required attribute aReq")

    def testDisplayBatch (self):
        instance = trac26.tAttributes()
        if DisplayException:
            instance.validateBinding()

    def testDisplayBatchReqFixed (self):
        instance = trac26.tAttributeReqFixed()
        if DisplayException:
            instance.validateBinding()

    def testDisplayDoc (self):
        if DisplayException:
            instance = trac26.CreateFromDocument(self.Bad_xmlt)

class TestProhibitedAttributeError (unittest.TestCase):
    Good_xmlt = six.u('<eAttributes aProhibited="6" aReq="4"/>')
    Good_xmld = Good_xmlt.encode('utf-8')
    Bad_xmlt = six.u('<eAttributesProhibited aProhibited="6" aReq="4"/>')
    Bad_xmld = Bad_xmlt.encode('utf-8')

    def testSchemaSupport (self):
        i1 = trac26.eAttributes(aReq=2, aProhibited=6)
        self.assertTrue(i1.validateBinding())
        i2 = trac26.eAttributesProhibited(aReq=2)
        self.assertTrue(i2.validateBinding())
        self.assertTrue(isinstance(i2, type(i1)))
        self.assertFalse(isinstance(i1, type(i2)))
        instance = trac26.CreateFromDocument(self.Good_xmlt)
        self.assertEqual(self.Good_xmld, instance.toxml('utf-8', root_only=True))

    def testConstructor (self):
        instance = None
        with self.assertRaises(pyxb.ProhibitedAttributeError) as cm:
            instance = trac26.eAttributesProhibited(aReq=2, aProhibited=6)

    def testAssignment (self):
        instance = trac26.eAttributesProhibited(aReq=2)
        with self.assertRaises(pyxb.ProhibitedAttributeError) as cm:
            instance.aProhibited = 6

    def testSet (self):
        instance = trac26.eAttributesProhibited(aReq=2)
        au = instance._AttributeMap['aProhibited']
        with self.assertRaises(pyxb.ProhibitedAttributeError) as cm:
            au.set(instance, 6)

    def testDocument (self):
        instance = None
        with self.assertRaises(pyxb.ProhibitedAttributeError) as cm:
            instance = trac26.CreateFromDocument(self.Bad_xmlt)
        e = cm.exception
        self.assertFalse(e.instance is None)
        self.assertEqual(e.type, trac26.tAttributesProhibited)
        self.assertFalse((e.location is None) and (pyxb.XMLStyle_saxer == pyxb._XMLStyle))
        if e.location is not None:
            self.assertEqual(1, e.location.lineNumber)
            self.assertEqual(0, e.location.columnNumber)
        self.assertEqual(str(e), "Attempt to reference prohibited attribute aProhibited in type <class 'trac26.tAttributesProhibited'>")

    def testDisplay (self):
        instance = trac26.eAttributesProhibited(aReq=2)
        if DisplayException:
            instance.aProhibited = 6

    def testDisplayDoc (self):
        if DisplayException:
            instance = trac26.CreateFromDocument(self.Bad_xmlt)

class TestUnrecognizedAttributeError (unittest.TestCase):
    Good_xmlt = six.u('<eAttributes aReq="4"/>')
    Good_xmld = Good_xmlt.encode('utf-8')
    Bad_xmlt = six.u('<eAttributes aReq="4" aBad="1"/>')
    Bad_xmld = Bad_xmlt.encode('utf-8')

    def testSchemaSupport (self):
        dom = pyxb.utils.domutils.StringToDOM(self.Good_xmlt)
        instance = trac26.CreateFromDOM(dom)
        self.assertEqual(self.Good_xmld, instance.toxml('utf-8', root_only=True))

    def testDOM (self):
        dom = pyxb.utils.domutils.StringToDOM(self.Bad_xmlt)
        with self.assertRaises(pyxb.UnrecognizedAttributeError) as cm:
            instance = trac26.CreateFromDOM(dom)
        e = cm.exception
        # The code path for this is creating a map from attribute tags
        # to values in isolation of the specific instance.  A
        # partially-constructed instance is available, but the
        # location is not available.
        self.assertEqual(e.type, trac26.tAttributes)
        self.assertEqual(e.tag, 'aBad')
        self.assertTrue(e.instance is not None)
        self.assertTrue(isinstance(e.instance, e.type))
        self.assertTrue(e.location is None)

    def testDocument (self):
        instance = None
        with self.assertRaises(pyxb.UnrecognizedAttributeError) as cm:
            instance = trac26.CreateFromDocument(self.Bad_xmlt)
        self.assertTrue(instance is None)
        e = cm.exception
        self.assertEqual(e.type, trac26.tAttributes)
        self.assertEqual(e.tag, 'aBad')
        # In this case we were given an instance, which provides a
        # location.  Note that initialization of the instance was left
        # incomplete.
        self.assertFalse(e.instance is None)
        self.assertFalse((e.location is None) and (pyxb.XMLStyle_saxer == pyxb._XMLStyle))
        if e.location is not None:
            self.assertEqual(1, e.location.lineNumber)
            self.assertEqual(0, e.location.columnNumber)

    def testDisplayDOM (self):
        if DisplayException:
            trac26.CreateFromDOM(pyxb.utils.domutils.StringToDOM(self.Bad_xmlt))

    def testDisplayDoc (self):
        if DisplayException:
            trac26.CreateFromDocument(self.Bad_xmlt)

class TestAttributeOnSimpleTypeError (unittest.TestCase):
    Good_xmlt = six.u('<eInts><eInt>1</eInt></eInts>')
    Good_xmld = Good_xmlt.encode('utf-8')
    Bad_xmlt = six.u('<eInts><eInt bits="1">1</eInt></eInts>')
    Bad_xmld = Bad_xmlt.encode('utf-8')

    def testSchemaSupport (self):
        instance = trac26.eInts(1,2)
        self.assertEqual(2, len(instance.eInt))
        e0 = instance.eInt[0]
        self.assertTrue(isinstance(e0, trac26.eInt.typeDefinition()))
        self.assertEqual(e0, 1)
        instance = trac26.CreateFromDocument(self.Good_xmlt)
        self.assertEqual(self.Good_xmld, instance.toxml('utf-8', root_only=True))

    def testException (self):
        instance = None
        with self.assertRaises(pyxb.AttributeOnSimpleTypeError) as cm:
            instance = trac26.CreateFromDocument(self.Bad_xmlt)
        e = cm.exception
        self.assertEqual(e.tag, 'bits')
        self.assertEqual(e.value, six.u('1'))
        self.assertFalse((e.location is None) and (pyxb.XMLStyle_saxer == pyxb._XMLStyle))
        if e.location is not None:
            self.assertEqual(1, e.location.lineNumber)
            self.assertEqual(7, e.location.columnNumber)
        self.assertEqual(str(e), "Simple type {http://www.w3.org/2001/XMLSchema}int cannot support attribute bits")

    def testDisplay (self):
        if DisplayException:
            instance = trac26.CreateFromDocument(self.Bad_xmlt)

class TestUnprocessedKeywordContentError (unittest.TestCase):
    def testException (self):
        instance = None
        with self.assertRaises(pyxb.UnprocessedKeywordContentError) as cm:
            instance = trac26.eAttributes(foo=3)
        self.assertTrue(instance is None)
        e = cm.exception
        self.assertTrue(isinstance(e.instance, trac26.tAttributes))
        self.assertEqual(1, len(e.keywords))
        self.assertEqual(3, e.keywords['foo'])
        self.assertTrue(e.location is None)
        self.assertEqual(str(e), 'Unprocessed keywords instantiating tAttributes: foo')

class TestExtraSimpleContentError (unittest.TestCase):

    def testSchemaSupport (self):
        instance = trac26.eCTwSC(1)
        self.assertTrue(instance.validateBinding())
        instance.reset()
        self.assertRaises(pyxb.SimpleContentAbsentError, instance.validateBinding)
        instance.append(1)
        self.assertTrue(instance.validateBinding())

    def testException (self):
        instance = trac26.eCTwSC(1)
        with self.assertRaises(pyxb.ExtraSimpleContentError) as cm:
            instance.append(2)
        e = cm.exception
        self.assertEqual(e.instance, instance)
        self.assertEqual(e.value, 2)
        self.assertTrue(e.location is None)
        self.assertEqual(str(e), 'Instance of tCTwSC already has simple content value assigned')

    def testDisplay (self):
        instance = trac26.eCTwSC(1)
        if DisplayException:
            instance.append(2)

class TestMixedContentError (unittest.TestCase):
    Good_xmlt = six.u('<eCTwSCSequence><eCTwSC>2</eCTwSC></eCTwSCSequence>')
    Good_xmld = Good_xmlt.encode('utf-8')
    Bad_xmlt = six.u('<eCTwSCSequence><eCTwSC>2</eCTwSC>noise</eCTwSCSequence>')
    Bad_xmld = Bad_xmlt.encode('utf-8')

    def testSchemaSupport (self):
        instance = trac26.eCTwSCSequence()
        instance.append(trac26.eCTwSC(2))
        instance = trac26.CreateFromDocument(self.Good_xmlt)
        self.assertEqual(self.Good_xmld, instance.toxml('utf-8', root_only=True))

    def testException (self):
        instance = trac26.eCTwSCSequence()
        instance.append(trac26.eCTwSC(2))
        with self.assertRaises(pyxb.MixedContentError) as cm:
            instance.append('noise')
        e = cm.exception
        self.assertTrue(e.location is None)
        self.assertEqual(e.instance, instance)
        self.assertEqual(e.value, 'noise')
        self.assertEqual(str(e), 'Invalid non-element content')

    def testDocument (self):
        instance = None
        with self.assertRaises(pyxb.MixedContentError) as cm:
            instance = trac26.CreateFromDocument(self.Bad_xmlt)
        e = cm.exception
        self.assertFalse((e.location is None) and (pyxb.XMLStyle_saxer == pyxb._XMLStyle))
        loctext = ''
        if e.location is not None:
            self.assertEqual(1, e.location.lineNumber)
            self.assertEqual(34, e.location.columnNumber)
            loctext = ' at <unknown>[1:34]'
        self.assertEqual(e.value, 'noise')
        self.assertEqual(str(e), 'Invalid non-element content{}'.format(loctext))

    def testDisplay (self):
        if DisplayException:
            instance = trac26.eCTwSCSequence()
            instance.append(trac26.eCTwSC(2))
            instance.append('noise')

    def testDisplayDoc (self):
        if DisplayException:
            instance = trac26.CreateFromDocument(self.Bad_xmlt)

class TestUnrecognizedContentError (unittest.TestCase):
    Good_xmlt = six.u('<eInts><eInt>1</eInt></eInts>')
    Good_xmld = Good_xmlt.encode('utf-8')
    Bad_xmlt = six.u('<eInts><eCTwSC>1</eCTwSC></eInts>')
    Bad_details = '''The containing element eIntsPlus is defined at trac26.xsd[80:2].
The containing element type <class 'trac26.CTD_ANON_3'> is defined at trac26.xsd[81:4]
The unrecognized content is eCTwSC
The <class 'trac26.CTD_ANON_3'> automaton is in an accepting state.
The following element and wildcard content would be accepted:
\tAn element eInt per trac26.xsd[83:8]
\tA wildcard per trac26.xsd[84:8]'''
    Bad2_xmlt = six.u('<eInts><something>1</something></eInts>')

    def testSchemaSupport (self):
        instance = trac26.eInts()
        instance.append(1)
        instance = trac26.CreateFromDocument(self.Good_xmlt)
        self.assertEqual(self.Good_xmld, instance.toxml('utf-8', root_only=True))

    def testException (self):
        instance = trac26.eIntsPlus()
        with self.assertRaises(pyxb.UnrecognizedContentError) as cm:
            instance.append(trac26.eCTwSC(2))
        e = cm.exception
        self.assertTrue(e.location is None)
        self.assertTrue(e.automaton_configuration is not None)
        self.assertTrue(isinstance(e.value, trac26.tCTwSC))
        acceptable = e.automaton_configuration.acceptableContent()
        self.assertEqual(2, len(acceptable))
        self.assertTrue(isinstance(acceptable[0], pyxb.binding.content.ElementUse))
        self.assertNotEqual(acceptable[0].elementBinding(), trac26.eInt)
        self.assertEqual(acceptable[0].typeDefinition(), trac26.eInt.typeDefinition())
        self.assertTrue(isinstance(acceptable[1], pyxb.binding.content.WildcardUse))
        self.assertEqual(str(e), 'Invalid content eCTwSC (expect eInt or xs:any)')
        if pyxb.XMLStyle_minidom != pyxb._XMLStyle:
            self.assertEqual(e.details(), self.Bad_details)

    def testDocument (self):
        instance = None
        with self.assertRaises(pyxb.UnrecognizedContentError) as cm:
            instance = trac26.CreateFromDocument(self.Bad_xmlt)
        e = cm.exception
        self.assertFalse((e.location is None) and (pyxb.XMLStyle_saxer == pyxb._XMLStyle))
        loctext = ''
        if e.location is not None:
            self.assertEqual(1, e.location.lineNumber)
            self.assertEqual(7, e.location.columnNumber)
            loctext= ' at <unknown>[1:7]'
        self.assertTrue(isinstance(e.value, trac26.tCTwSC))
        self.assertEqual(e._valueDescription(), 'eCTwSC')
        acceptable = e.automaton_configuration.acceptableContent()
        self.assertEqual(1, len(acceptable))
        self.assertNotEqual(acceptable[0].elementBinding(), trac26.eInt)
        self.assertEqual(acceptable[0].typeDefinition(), trac26.eInt.typeDefinition())
        self.assertEqual(str(e), 'Invalid content eCTwSC{} (expect eInt)'.format(loctext))

    def testDocument2 (self):
        instance = None
        with self.assertRaises(pyxb.UnrecognizedContentError) as cm:
            instance = trac26.CreateFromDocument(self.Bad2_xmlt)
        e = cm.exception
        self.assertFalse((e.location is None) and (pyxb.XMLStyle_saxer == pyxb._XMLStyle))
        loctext = ''
        if e.location is not None:
            self.assertEqual(1, e.location.lineNumber)
            self.assertEqual(7, e.location.columnNumber)
            loctext= ' at <unknown>[1:7]'
        self.assertTrue(isinstance(e.value, xml.dom.Node))
        self.assertFalse(isinstance(e.value, pyxb.binding.basis._TypeBinding_mixin))
        self.assertEqual(e._valueDescription(), 'something')
        acceptable = e.automaton_configuration.acceptableContent()
        self.assertEqual(1, len(acceptable))
        self.assertNotEqual(acceptable[0].elementBinding(), trac26.eInt)
        self.assertEqual(acceptable[0].typeDefinition(), trac26.eInt.typeDefinition())
        self.assertEqual(str(e), 'Invalid content something{} (expect eInt)'.format(loctext))

    def testDisplay (self):
        if DisplayException:
            instance = trac26.eInts()
            instance.append(trac26.eCTwSC(2))

    def testDisplayDoc (self):
        if DisplayException:
            instance = trac26.CreateFromDocument(self.Bad_xmlt)

class TestIncompleteElementContentError (unittest.TestCase):
    Good_xmlt = six.u('<eTranslateCard><eConcCardCymru>un</eConcCardCymru><eConcCardEnglish>one</eConcCardEnglish><cardinal>1</cardinal></eTranslateCard>')
    Good_xmld = Good_xmlt.encode('utf-8')
    Bad_xmlt = six.u('<eTranslateCard><eConcCardEnglish>one</eConcCardEnglish><cardinal>1</cardinal></eTranslateCard>')
    Bad_xmld = Bad_xmlt.encode('utf-8')
    Bad_details = '''The containing element eTranslateCard is defined at trac26.xsd[124:2].
The containing element type tTranslateCard is defined at trac26.xsd[115:2]
The tTranslateCard automaton is not in an accepting state.
The last accepted content was eConcCardCymru
The following element and wildcard content would be accepted:
\tAn element eConcCardEnglish per trac26.xsd[119:8]
The following content was not processed by the automaton:
\tcardinal (1 instances)'''
    Bad_details_noloc = '''The containing element eTranslateCard is defined at None.
The containing element type tTranslateCard is defined at None
The tTranslateCard automaton is not in an accepting state.
The last accepted content was eConcCardCymru
The following element and wildcard content would be accepted:
\tAn element eConcCardEnglish per None
The following content was not processed by the automaton:
\tcardinal (1 instances)'''

    def testSchemaSupport (self):
        instance = trac26.eTranslateCard(trac26.eConcCardCymru('un'),
                                         trac26.eConcCardEnglish('one'),
                                         xs.int(1))
        self.assertTrue(instance.validateBinding())
        instance = trac26.CreateFromDocument(self.Good_xmlt)
        self.assertEqual(self.Good_xmld, instance.toxml('utf-8', root_only=True))
        instance = trac26.eTranslateCard(trac26.eConcCardCymru('un'))
        instance.cardinal = 1
        instance.eConcCardEnglish = 'one'
        self.assertTrue(instance.validateBinding())

    def testException (self):
        instance = trac26.eTranslateCard(trac26.eConcCardCymru('un'))
        instance.cardinal = 1
        with self.assertRaises(pyxb.IncompleteElementContentError) as cm:
            instance.validateBinding()
        e = cm.exception
        self.assertFalse(e.fac_configuration.isAccepting())
        self.assertEqual(1, len(e.symbols))
        self.assertEqual(1, len(e.symbol_set))
        (ed, syms) = next(six.iteritems(e.symbol_set))
        self.assertEqual(1, len(syms))
        self.assertEqual(instance.cardinal, syms[0])
        expect = self.Bad_details
        if pyxb.XMLStyle_minidom == pyxb._XMLStyle:
            expect = self.Bad_details_noloc
        self.assertEqual(e.details(), expect)

class TestUnprocessedElementContentError (unittest.TestCase):
    Bad_details = '''The containing element eTranslateCardMulti is defined at trac26.xsd[132:2].
The containing element type tTranslateCardMulti is defined at trac26.xsd[125:2]
The tTranslateCardMulti automaton is in an accepting state.
The last accepted content was cardinal
The following element and wildcard content would be accepted:
\tAn element eConcCardCymru per trac26.xsd[127:6]
The following content was not processed by the automaton:
\tcardinal (1 instances)'''

    def testSchemaSupport (self):
        instance = trac26.eTranslateCardMulti(trac26.eConcCardCymru('un'),
                                              trac26.eConcCardEnglish('one'),
                                              xs.int(1))
        self.assertTrue(instance.validateBinding())
        instance.eConcCardCymru.append('dau')
        instance.eConcCardEnglish.append('two')
        instance.cardinal.append(2)
        self.assertTrue(instance.validateBinding())

    def testException (self):
        instance = trac26.eTranslateCardMulti(trac26.eConcCardCymru('un'),
                                              trac26.eConcCardEnglish('one'),
                                              xs.int(1))
        self.assertTrue(instance.validateBinding())
        instance.cardinal.append(2)
        with self.assertRaises(pyxb.UnprocessedElementContentError) as cm:
            instance.validateBinding()
        e = cm.exception
        self.assertTrue(e.fac_configuration.isAccepting())
        self.assertEqual(3, len(e.symbols))
        self.assertEqual(1, len(e.symbol_set))
        (ed, syms) = next(six.iteritems(e.symbol_set))
        self.assertEqual(1, len(syms))
        self.assertEqual(instance.cardinal[1], syms[0])
        if pyxb.XMLStyle_minidom != pyxb._XMLStyle:
            self.assertEqual(e.details(), self.Bad_details)

class TestContentInNilInstanceError (unittest.TestCase):
    Good_xmlt = six.u('<eNilCTwSC xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:nil="true"/>')
    Good_xmld = Good_xmlt.encode('utf-8')
    Bad_xmlt = six.u('<eNilCTwSC xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:nil="true">4</eNilCTwSC>')
    Bad_xmld = Bad_xmlt.encode('utf-8')

    def testSchemaSupport (self):
        instance = trac26.eNilCTwSC(4)
        self.assertEqual(instance.value(), 4)
        self.assertTrue(instance.validateBinding())
        instance = trac26.eNilCTwSC(_nil=True)
        self.assertTrue(instance.value() is None)
        self.assertTrue(instance.validateBinding())
        instance = trac26.CreateFromDocument(self.Good_xmlt)
        self.assertEqual(self.Good_xmld, instance.toxml('utf-8', root_only=True))
        instance = trac26.eNilInt(4)
        self.assertEqual(4, instance)
        instance = trac26.eNilInt(_nil=True)
        self.assertTrue(instance.validateBinding())
        instance = trac26.eNilCTwSC(3)
        instance.reset()
        instance.append(4)
        self.assertTrue(instance.validateBinding())
        instance = trac26.eNilOneInt()
        instance.eInt = 5
        self.assertTrue(instance.validateBinding())
        instance = trac26.eNilInts()
        instance.eInt.append(1)
        self.assertTrue(instance.validateBinding())

    def testConstructor (self):
        with self.assertRaises(pyxb.ContentInNilInstanceError) as cm:
            trac26.eNilInt(4, _nil=True)
        e = cm.exception
        self.assertTrue(e.location is None)
        self.assertEqual(e.instance._element(), trac26.eNilInt)
        self.assertEqual(e.content, 4)

    def testAppend (self):
        instance = trac26.eNilCTwSC(_nil=True)
        with self.assertRaises(pyxb.ContentInNilInstanceError) as cm:
            instance.append(4)
        e = cm.exception
        self.assertTrue(e.location is None)
        self.assertEqual(e.content, 4)

    def testValidate (self):
        instance = trac26.eNilInts(1, 2, 3)
        self.assertTrue(instance.validateBinding())
        instance._setIsNil(True)
        self.assertTrue(instance.validateBinding())
        # Not a valid way to do things, but only way to test this raise
        instance.content().append(1)
        with self.assertRaises(pyxb.ContentInNilInstanceError) as cm:
            instance.validateBinding()
        e = cm.exception
        self.assertTrue(e.location is None)
        self.assertEqual(e.content, [1])

    def testContentAppend (self):
        instance = trac26.eNilInts(_nil=True)
        self.assertTrue(instance._isNil())
        with self.assertRaises(pyxb.ContentInNilInstanceError) as cm:
            type(instance)._UseForTag('eInt').append(instance, 1)
        e = cm.exception
        self.assertTrue(e.location is None)
        self.assertEqual(e.instance, instance)

    def testContentSet (self):
        instance = trac26.eNilOneInt(_nil=True)
        with self.assertRaises(pyxb.ContentInNilInstanceError) as cm:
            instance.eInt = 1
        e = cm.exception
        self.assertTrue(e.location is None)
        self.assertEqual(e.instance, instance)

    def testDocument (self):
        instance = None
        with self.assertRaises(pyxb.ContentInNilInstanceError) as cm:
            instance = trac26.CreateFromDocument(self.Bad_xmlt)
        e = cm.exception
        self.assertFalse(e.location is None)
        self.assertEqual(e.content, six.u('4'))
        self.assertEqual(1, e.location.lineNumber)
        self.assertEqual(0, e.location.columnNumber)
        self.assertEqual(str(e), 'eNilCTwSC with {http://www.w3.org/2001/XMLSchema-instance}nil=true cannot have content')

    def testDisplayDoc (self):
        if DisplayException:
            trac26.CreateFromDocument(self.Bad_xmlt)

class TestContentInNilInstanceError (unittest.TestCase):
    def testSchemaSupport (self):
        instance = trac26.eNilCTwSC(4)
        instance._setIsNil(True)
        self.assertTrue(instance.validateBinding())

    def testException (self):
        instance = trac26.eCTwSC(4)
        with self.assertRaises(pyxb.NoNillableSupportError) as cm:
            instance._setIsNil(True)
        e = cm.exception
        self.assertTrue(e.location is None)
        self.assertEqual(e.instance, instance)

class TestSimpleListValueError (unittest.TestCase):
    # Note: Unable to come up with code to test raise in _CheckValidValue;
    # values get validated before that point.
    Good_xmlt = six.u('<eListCardCymru>un dau tri pedwar</eListCardCymru>')
    Good_xmld = Good_xmlt.encode('utf-8')
    Bad_xmlt = six.u('<eListCardCymru>un dau tri pedwar pump</eListCardCymru>')
    Bad_xmld = Bad_xmlt.encode('utf-8')

    def testSchemaSupport (self):
        instance = trac26.eListCardCymru()
        instance.append('un')
        instance.append('dau')
        self.assertTrue(instance.validateBinding())
        instance = trac26.CreateFromDocument(self.Good_xmlt)
        self.assertEqual(self.Good_xmld, instance.toxml('utf-8', root_only=True))
        instance = trac26.eSimpleInstance()
        self.assertTrue(instance.validateBinding())
        instance.eSimpleInstance = [ 'un', 'dau', 'tri' ]
        self.assertTrue(instance.validateBinding())

    def testException (self):
        instance = trac26.eListCardCymru()
        with self.assertRaises(pyxb.SimpleListValueError) as cm:
            instance.append('pump')
        e = cm.exception
        self.assertEqual(e.type, trac26.tListCardCymru)
        self.assertEqual(e.value, 'pump')
        self.assertTrue(e.location is None)
        self.assertEqual(str(e), 'Member type tCardCymru of list type tListCardCymru cannot accept pump')

    def testException (self):
        instance = None
        with self.assertRaises(pyxb.SimpleListValueError) as cm:
            instance = trac26.CreateFromDocument(self.Bad_xmlt)
        e = cm.exception
        self.assertEqual(e.type, trac26.tListCardCymru)
        self.assertEqual(e.value, 'pump')
        self.assertFalse((e.location is None) and (pyxb.XMLStyle_saxer == pyxb._XMLStyle))
        if e.location is not None:
            self.assertEqual(1, e.location.lineNumber)
            self.assertEqual(0, e.location.columnNumber)

class TestSimpleUnionValueError (unittest.TestCase):
    Good_xmlt = six.u('<eSimpleInstance><eUnionCard>dau</eUnionCard></eSimpleInstance>')
    Good_xmld = Good_xmlt.encode('utf-8')
    Bad_xmlt = six.u('<eSimpleInstance><eUnionCard>pump</eUnionCard></eSimpleInstance>')
    Bad_xmld = Bad_xmlt.encode('utf-8')

    def testSchemaSupport (self):
        for (ty, va) in ((trac26.tCardCymru, 'un'), (trac26.tCardEnglish, 'two') , (xs.int, 3)):
            instance = trac26.eUnionCard(va)
            self.assertTrue(isinstance(instance, ty))
            xmlt = six.u('<eUnionCard>%s</eUnionCard>') % (va,)
            xmld = xmlt.encode('utf-8')
            self.assertEqual(xmld, instance.toxml('utf-8', root_only=True))
        instance = trac26.CreateFromDocument(self.Good_xmlt)
        self.assertEqual(self.Good_xmld, instance.toxml('utf-8', root_only=True))

    def testException (self):
        instance = None
        with self.assertRaises(pyxb.SimpleUnionValueError) as cm:
            instance = trac26.eUnionCard('pump')
        e = cm.exception
        self.assertEqual(e.type, trac26.tUnionCard)
        self.assertEqual(e.value, ('pump',))
        self.assertTrue(e.location is None)
        self.assertEqual(str(e), "No memberType of tUnionCard can be constructed from ('pump',)")

    def testDocument (self):
        instance = None
        with self.assertRaises(pyxb.SimpleUnionValueError) as cm:
            instance = trac26.CreateFromDocument(self.Bad_xmlt)
        e = cm.exception
        self.assertEqual(e.type, trac26.tUnionCard)
        if pyxb.XMLStyle_saxer == pyxb._XMLStyle:
            self.assertEqual(e.value, ('pump',))
            self.assertFalse(e.location is None)
            self.assertEqual(1, e.location.lineNumber)
            self.assertEqual(17, e.location.columnNumber)

class TestSimpleFacetValueError (unittest.TestCase):
    Good_xmlt = six.u('<eTLA>ABC</eTLA>')
    Good_xmld = Good_xmlt.encode('utf-8')
    Bad_xmlt = six.u('<eTLA>ABCD</eTLA>')
    Bad_xmld = Bad_xmlt.encode('utf-8')

    def testSchemaSupport (self):
        instance = trac26.eTLA('ABC')
        self.assertTrue(instance.validateBinding())
        instance = trac26.CreateFromDocument(self.Good_xmlt)
        self.assertEqual(self.Good_xmld, instance.toxml('utf-8', root_only=True))

    def testException (self):
        instance = None
        with self.assertRaises(pyxb.SimpleFacetValueError) as cm:
            instance = trac26.eTLA('ABCD')
        e = cm.exception
        self.assertTrue(e.location is None)
        self.assertEqual(e.type, trac26.tTLA)
        self.assertEqual(e.value, 'ABCD')
        self.assertEqual(e.facet, trac26.tTLA._CF_length)
        self.assertEqual(str(e), 'Type tTLA length constraint violated by value ABCD')

    def testDocument (self):
        instance = None
        with self.assertRaises(pyxb.SimpleFacetValueError) as cm:
            instance = trac26.CreateFromDocument(self.Bad_xmlt)
        e = cm.exception
        self.assertFalse((e.location is None) and (pyxb.XMLStyle_saxer == pyxb._XMLStyle))
        if e.location is not None:
            self.assertEqual(1, e.location.lineNumber)
            self.assertEqual(0, e.location.columnNumber)
        self.assertEqual(e.type, trac26.tTLA)
        self.assertEqual(e.value, 'ABCD')
        self.assertEqual(e.facet, trac26.tTLA._CF_length)
        self.assertEqual(str(e), 'Type tTLA length constraint violated by value ABCD')

if __name__ == '__main__':
    if sys.version_info[:2] >= (2, 7):
        unittest.main()
    else:
        _log.warning('Cannot run test prior to Python 2.7')
