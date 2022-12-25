# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import unittest
from pyxb.utils.utility import *
from pyxb.utils.utility import _DeconflictSymbols_mixin
from pyxb.utils import six
import sys

class DST_base (_DeconflictSymbols_mixin):
    _ReservedSymbols = set([ 'one', 'two' ])

class DST_sub (DST_base):
    _ReservedSymbols = DST_base._ReservedSymbols.union(set([ 'three' ]))

class DeconfictSymbolsTtest (unittest.TestCase):
    def testDeconflict (self):
        self.assertEqual(2, len(DST_base._ReservedSymbols))
        self.assertEqual(3, len(DST_sub._ReservedSymbols))

if six.PY3:
    def qu(s):
        return '"' + s.replace('"', '\\"') + '"'
else:
    def qu(s):
        s = unicode(s.replace(r'\\', r'\\\\'), "unicode_escape")
        return six.u('u"') + s.replace('"', '\\"') + '"'

class BasicTest (unittest.TestCase):

    cases = ( ( r'"1\x042"', "1\0042" ) # expanded octal
            , ( r'"1\x042"', '1\0042' ) # expanded octal (single quotes do not affect escaping)
            , ( "r'1\\0042'", r'1\0042' ) # preserve unexpanded octal
            , ( r'"1\x222&3"', '1"2&3' )  # escape double quotes
            , ( '"one\'two"', "one'two" ) # preserve single quote
            , ( r'"1\n2"', "1\n2" )       # expanded newline to escape sequence
            , ( "r'1\\n2'", r'1\n2' )     # raw backslash preserved
            , ( "\"1'\\n'2\"", "1'\n'2" ) # expanded newline to escape sequence
            , ( "\"1'\\n'2\"", '1\'\n\'2' ) # expanded newline to escape sequence (single quotes)
            , ( "\"1\\x22\\n\\x222\"", '1"\n"2' ) # escape double quotes around expanded newline
            , ( "r'1\\'\\n\\'2'", r'1\'\n\'2' )   # preserve escaped quote and newline
            , ( qu(r'"1\u00042"'), six.u("1\0042") )       # unicode expanded octal
            , ( qu(r'"1\u00222&3"'), six.u('1"2&3') )      # unicode escape double quotes
            , ( qu(r'"one' + "'" + r'two"'), six.u("one'two") ) # unicode embedded single quote
            , ( "r'\\i\\c*'", r'\i\c*' )               # backslashes as in patterns
            , ( qu('"0"'), six.u('\u0030') )                   # expanded unicode works
            , ( qu('"\\u0022"'), six.u('"') )      # unicode double quotes are escaped
            , ( qu('"\\u0022"'), six.u('\u0022') ) # single quotes don't change that expanded unicode works
            , ( qu('"\\u0022"'), six.u(r'\u0022') ) # raw has no effect on unicode escapes
            , ( qu('\"'), six.u("'") )           # unicode single quote works
            , ( qu('\"\\u00220\\u0022\"'), six.u('"\u0030"') ) # unicode with double quotes works
            )


    def testPrepareIdentifier (self):
        in_use = set()
        self.assertEqual('id', PrepareIdentifier('id', in_use))
        self.assertEqual('id_', PrepareIdentifier('id', in_use))
        self.assertEqual('id_2', PrepareIdentifier('id_', in_use))
        self.assertEqual('id_3', PrepareIdentifier('id____', in_use))
        self.assertEqual('_id', PrepareIdentifier('id', in_use, protected=True))
        self.assertEqual('_id_', PrepareIdentifier('id', in_use, protected=True))
        self.assertEqual('__id', PrepareIdentifier('id', in_use, private=True))
        self.assertEqual('__id_', PrepareIdentifier('id', in_use, private=True))

        reserved = frozenset([ 'Factory' ])
        in_use = set()
        self.assertEqual('Factory_', PrepareIdentifier('Factory', in_use, reserved))
        self.assertEqual('Factory_2', PrepareIdentifier('Factory', in_use, reserved))
        self.assertEqual('Factory_3', PrepareIdentifier('Factory', in_use, reserved))

        in_use = set()
        self.assertEqual('global_', PrepareIdentifier('global', in_use))
        self.assertEqual('global_2', PrepareIdentifier('global', in_use))
        self.assertEqual('global_3', PrepareIdentifier('global', in_use))

        in_use = set()
        self.assertEqual('n24_hours', PrepareIdentifier('24 hours', in_use))

    def testQuotedEscape (self):
        for ( expected, input ) in self.cases:
            result = QuotedEscaped(input)
            # Given "expected" value may not be correct.  Don't care as
            # long as the evalution produces the input.
            #self.assertEqual(expected, result)
            self.assertEqual(input, eval(result))

    def testMakeIdentifier (self):
        self.assertEqual('id', MakeIdentifier('id'))
        self.assertEqual('id', MakeIdentifier(six.u('id')))
        self.assertEqual('id_sep', MakeIdentifier(six.u('id_sep')))
        self.assertEqual('id_sep', MakeIdentifier(six.u('id sep')))
        self.assertEqual('id_sep_too', MakeIdentifier(six.u('id-sep too')))
        self.assertEqual('idid', MakeIdentifier(six.u('id&id')))
        self.assertEqual('id', MakeIdentifier('_id'))
        self.assertEqual('id_', MakeIdentifier('_id_'))
        self.assertEqual('emptyString', MakeIdentifier(''))
        self.assertEqual('emptyString', MakeIdentifier('_'))

    def testCamelCase (self):
        self.assertEqual('one_and_two', MakeIdentifier('one_and_two'))
        self.assertEqual('one_and_two', MakeIdentifier('one-and-two'))
        self.assertEqual('oneAndTwo', MakeIdentifier('one_and_two', camel_case=True))
        self.assertEqual('oneAndTwo', MakeIdentifier('one-and-two', camel_case=True))

    def testDeconflictKeyword (self):
        self.assertEqual('id', DeconflictKeyword('id'))
        self.assertEqual('for_', DeconflictKeyword('for'))

    def testMakeUnique (self):
        in_use = set()
        self.assertEqual('id', MakeUnique('id', in_use))
        self.assertEqual(1, len(in_use))
        self.assertEqual('id_', MakeUnique('id', in_use))
        self.assertEqual(2, len(in_use))
        self.assertEqual('id_2', MakeUnique('id', in_use))
        self.assertEqual(3, len(in_use))
        self.assertEqual(set(( 'id', 'id_', 'id_2' )), in_use)

class TestGraph (unittest.TestCase):

    _Edges = [
        (1, 2),
        (2, 3),
        (2, 4),
        (4, 8),
        (5, 6),
        (5, 7),
        (6, 10),
        (7, 8),
        (8, 5),
        (8, 9),
        (9, 10),
        (10, 0)
        ]

    def testRoot (self):
        graph = Graph()
        [ graph.addEdge(*_e) for _e in self._Edges ]
        roots = graph.roots().copy()
        self.assertEqual(1, len(roots))
        self.assertEqual(1, roots.pop())

    def testTarjan (self):
        graph = Graph()
        [ graph.addEdge(*_e) for _e in self._Edges ]
        scc = graph.scc()
        self.assertEqual(1, len(scc))
        self.assertEqual(set([5, 7, 8]), set(scc[0]))

    def testRootIsNode (self):
        graph = Graph()
        graph.addRoot(4)
        self.assertEqual(1, len(graph.nodes()))
        self.assertEqual(graph.roots(), graph.nodes())

    def testDFSOrder1 (self):
        graph = Graph()
        [ graph.addEdge(*_e) for _e in self._Edges ]
        order = graph.dfsOrder()
        self.assertTrue(isinstance(order, list))
        self.assertEqual(len(graph.nodes()), len(order))
        walked = set()
        for source in order:
            for target in graph.edgeMap().get(source, []):
                self.assertTrue((target in walked) or (graph.sccForNode(source) == graph.sccForNode(target)), '%s -> %s not satisfied, seen' % (source, target))
            walked.add(source)
        order = graph.sccOrder()
        self.assertEqual(len(graph.nodes()), len(order) + 2)
        walked = set()
        for source in order:
            if isinstance(source, list):
                walked.update(source)
                continue
            for target in graph.edgeMap().get(source, []):
                self.assertTrue((target in walked) or (graph.sccForNode(source) == graph.sccForNode(target)), '%s -> %s not satisfied, seen' % (source, target))
            walked.add(source)

    def testDFSOrder2 (self):
        graph = Graph()
        graph.addEdge(2, 2)
        graph.addEdge(2, 1)
        graph.addNode(3)
        order = graph.dfsOrder()
        self.assertTrue(isinstance(order, list))
        self.assertEqual(len(graph.nodes()), len(order))
        walked = set()
        for source in order:
            for target in graph.edgeMap().get(source, []):
                self.assertTrue((target in walked) or (graph.sccForNode(source) == graph.sccForNode(target)), '%s -> %s not satisfied, seen' % (source, target))
            walked.add(source)

    def testDFSOrder_Loop (self):
        graph = Graph()
        graph.addEdge(1, 2)
        graph.addEdge(2, 3)
        graph.addEdge(3, 1)
        self.assertEqual(0, len(graph.roots()))
        self.assertRaises(Exception, graph.dfsOrder)
        graph.addRoot(1)
        self.assertEqual(1, len(graph.roots()))
        scc = graph.scc()
        self.assertEqual(1, len(scc))
        self.assertEqual(set([1, 2, 3]), set(scc[0]))

    def testDFSOrder4 (self):
        graph = Graph()
        graph.addEdge('gmd.applicationSchema', 'gco.basicTypes')
        graph.addEdge('gmd.applicationSchema', 'gmd.applicationSchema')
        graph.addEdge('gmd.applicationSchema', 'xlink.xlinks')
        graph.addEdge('gmd.applicationSchema', 'gco.gcoBase')
        graph.addEdge('gmd.applicationSchema', 'gmd.citation')
        graph.addEdge('gmd.applicationSchema', 'gml.basicTypes')
        graph.addEdge('gmd.portrayalCatalogue', 'gco.gcoBase')
        graph.addEdge('gmd.portrayalCatalogue', 'gmd.portrayalCatalogue')
        graph.addEdge('gmd.portrayalCatalogue', 'gmd.citation')
        graph.addEdge('gmd.portrayalCatalogue', 'xlink.xlinks')
        graph.addEdge('gmd.portrayalCatalogue', 'gml.basicTypes')
        graph.addEdge('gmd.freeText', 'gmd.freeText')
        graph.addEdge('gmd.freeText', 'gco.gcoBase')
        graph.addEdge('gmd.freeText', 'gco.basicTypes')
        graph.addEdge('gmd.freeText', 'gmd.citation')
        graph.addEdge('gmd.freeText', 'gmd.identification')
        graph.addEdge('gmd.freeText', 'gml.basicTypes')
        graph.addEdge('gmd.freeText', 'xlink.xlinks')
        graph.addEdge('gmd.dataQuality', 'gco.basicTypes')
        graph.addEdge('gmd.dataQuality', 'xlink.xlinks')
        graph.addEdge('gmd.dataQuality', 'gco.gcoBase')
        graph.addEdge('gmd.dataQuality', 'gmd.referenceSystem')
        graph.addEdge('gmd.dataQuality', 'gmd.maintenance')
        graph.addEdge('gmd.dataQuality', 'gmd.extent')
        graph.addEdge('gmd.dataQuality', 'gmd.citation')
        graph.addEdge('gmd.dataQuality', 'gmd.identification')
        graph.addEdge('gmd.dataQuality', 'gml.basicTypes')
        graph.addEdge('gmd.dataQuality', 'gmd.dataQuality')
        graph.addEdge('gmd.metadataApplication', 'gml.basicTypes')
        graph.addEdge('gmd.metadataApplication', 'gco.gcoBase')
        graph.addEdge('gmd.metadataApplication', 'gmd.metadataEntity')
        graph.addEdge('gmd.metadataApplication', 'gmd.metadataApplication')
        graph.addEdge('gmd.metadataApplication', 'xlink.xlinks')
        graph.addEdge('gmd.spatialRepresentation', 'gco.gcoBase')
        graph.addEdge('gmd.spatialRepresentation', 'gss.geometry')
        graph.addEdge('gmd.spatialRepresentation', 'gml.basicTypes')
        graph.addEdge('gmd.spatialRepresentation', 'gco.basicTypes')
        graph.addEdge('gmd.spatialRepresentation', 'gmd.citation')
        graph.addEdge('gmd.spatialRepresentation', 'xlink.xlinks')
        graph.addEdge('gmd.spatialRepresentation', 'gmd.spatialRepresentation')
        graph.addEdge('gmd.extent', 'gco.basicTypes')
        graph.addEdge('gmd.extent', 'gts.temporalObjects')
        graph.addEdge('gmd.extent', 'gco.gcoBase')
        graph.addEdge('gmd.extent', 'gmd.extent')
        graph.addEdge('gmd.extent', 'gml.basicTypes')
        graph.addEdge('gmd.extent', 'gmd.referenceSystem')
        graph.addEdge('gmd.extent', 'xlink.xlinks')
        graph.addEdge('gmd.extent', 'gss.geometry')
        graph.addEdge('gmd.extent', 'gsr.spatialReferencing')
        graph.addEdge('gmd.distribution', 'gmd.distribution')
        graph.addEdge('gmd.distribution', 'gml.basicTypes')
        graph.addEdge('gmd.distribution', 'gco.gcoBase')
        graph.addEdge('gmd.distribution', 'gco.basicTypes')
        graph.addEdge('gmd.distribution', 'gmd.citation')
        graph.addEdge('gmd.distribution', 'xlink.xlinks')
        graph.addEdge('gmd.metadataExtension', 'gml.basicTypes')
        graph.addEdge('gmd.metadataExtension', 'gco.gcoBase')
        graph.addEdge('gmd.metadataExtension', 'gco.basicTypes')
        graph.addEdge('gmd.metadataExtension', 'gmd.metadataExtension')
        graph.addEdge('gmd.metadataExtension', 'gmd.citation')
        graph.addEdge('gmd.metadataExtension', 'xlink.xlinks')
        graph.addEdge('gmd.maintenance', 'gts.temporalObjects')
        graph.addEdge('gmd.maintenance', 'gco.gcoBase')
        graph.addEdge('gmd.maintenance', 'gmd.maintenance')
        graph.addEdge('gmd.maintenance', 'gco.basicTypes')
        graph.addEdge('gmd.maintenance', 'gmd.citation')
        graph.addEdge('gmd.maintenance', 'gml.basicTypes')
        graph.addEdge('gmd.maintenance', 'xlink.xlinks')
        graph.addEdge('gmd.identification', 'gco.basicTypes')
        graph.addEdge('gmd.identification', 'xlink.xlinks')
        graph.addEdge('gmd.identification', 'gco.gcoBase')
        graph.addEdge('gmd.identification', 'gmd.referenceSystem')
        graph.addEdge('gmd.identification', 'gmd.maintenance')
        graph.addEdge('gmd.identification', 'gmd.extent')
        graph.addEdge('gmd.identification', 'gmd.distribution')
        graph.addEdge('gmd.identification', 'gmd.citation')
        graph.addEdge('gmd.identification', 'gmd.identification')
        graph.addEdge('gmd.identification', 'gml.basicTypes')
        graph.addEdge('gmd.identification', 'gmd.constraints')
        graph.addEdge('gmd.metadataEntity', 'gmd.content')
        graph.addEdge('gmd.metadataEntity', 'gco.basicTypes')
        graph.addEdge('gmd.metadataEntity', 'gmd.portrayalCatalogue')
        graph.addEdge('gmd.metadataEntity', 'gmd.metadataApplication')
        graph.addEdge('gmd.metadataEntity', 'gco.gcoBase')
        graph.addEdge('gmd.metadataEntity', 'gml.basicTypes')
        graph.addEdge('gmd.metadataEntity', 'gmd.applicationSchema')
        graph.addEdge('gmd.metadataEntity', 'gmd.metadataEntity')
        graph.addEdge('gmd.metadataEntity', 'gmd.referenceSystem')
        graph.addEdge('gmd.metadataEntity', 'gmd.maintenance')
        graph.addEdge('gmd.metadataEntity', 'gmd.metadataExtension')
        graph.addEdge('gmd.metadataEntity', 'gmd.distribution')
        graph.addEdge('gmd.metadataEntity', 'gmd.freeText')
        graph.addEdge('gmd.metadataEntity', 'gmd.identification')
        graph.addEdge('gmd.metadataEntity', 'gmd.constraints')
        graph.addEdge('gmd.metadataEntity', 'xlink.xlinks')
        graph.addEdge('gmd.metadataEntity', 'gmd.citation')
        graph.addEdge('gmd.metadataEntity', 'gmd.dataQuality')
        graph.addEdge('gmd.metadataEntity', 'gmd.spatialRepresentation')
        graph.addEdge('gmd.constraints', 'gco.gcoBase')
        graph.addEdge('gmd.constraints', 'gco.basicTypes')
        graph.addEdge('gmd.constraints', 'gmd.constraints')
        graph.addEdge('gmd.constraints', 'xlink.xlinks')
        graph.addEdge('gmd.constraints', 'gml.basicTypes')
        graph.addEdge('gmd.content', 'gmd.content')
        graph.addEdge('gmd.content', 'gco.basicTypes')
        graph.addEdge('gmd.content', 'xlink.xlinks')
        graph.addEdge('gmd.content', 'gco.gcoBase')
        graph.addEdge('gmd.content', 'gmd.referenceSystem')
        graph.addEdge('gmd.content', 'gmd.citation')
        graph.addEdge('gmd.content', 'gml.basicTypes')
        graph.addEdge('gmd.referenceSystem', 'gco.gcoBase')
        graph.addEdge('gmd.referenceSystem', 'gco.basicTypes')
        graph.addEdge('gmd.referenceSystem', 'gmd.referenceSystem')
        graph.addEdge('gmd.referenceSystem', 'gmd.extent')
        graph.addEdge('gmd.referenceSystem', 'gmd.citation')
        graph.addEdge('gmd.referenceSystem', 'gml.basicTypes')
        graph.addEdge('gmd.referenceSystem', 'xlink.xlinks')
        graph.addEdge('gmd.citation', 'gco.gcoBase')
        graph.addEdge('gmd.citation', 'gml.basicTypes')
        graph.addEdge('gmd.citation', 'gco.basicTypes')
        graph.addEdge('gmd.citation', 'gmd.referenceSystem')
        graph.addEdge('gmd.citation', 'gmd.citation')
        graph.addEdge('gmd.citation', 'xlink.xlinks')

        self.assertEqual(23, len(graph.nodes()))
        self.assertEqual(123, len(graph.edges()))
        self.assertRaises(Exception, graph.dfsOrder)

    def testDFSOrder5 (self):
        graph = Graph()
        graph.addEdge(1, 2)
        graph.addEdge(1, 3)
        graph.addEdge(3, 4)
        graph.addEdge(3, 5)
        graph.addEdge(5, 1)
        graph.addEdge(5, 6)
        graph.addEdge(6, 2)
        self.assertRaises(Exception, graph.scc)
        self.assertRaises(Exception, graph.dfsOrder)
        graph.addRoot(1)
        order = graph.sccOrder(reset=True)
        self.assertEqual(4, len(order))
        self.assertEqual(1, len(graph.scc()))
        self.assertEqual(set([1, 3, 5]), set(graph.scc()[0]))

import tempfile

class _TestOpenOrCreate_mixin (object):
    def setUp (self):
        tf = tempfile.NamedTemporaryFile()
        self.__fileName = tf.name
        tf.close()

    def fileName (self):
        return self.__fileName

    def unlinkFile (self):
        try:
            os.unlink(self.__fileName)
        except OSError as e:
            if errno.ENOENT != e:
                raise

    def tearDown (self):
        self.unlinkFile()

class TestOpenOrCreate_New (unittest.TestCase, _TestOpenOrCreate_mixin):
    setUp = _TestOpenOrCreate_mixin.setUp
    tearDown = _TestOpenOrCreate_mixin.tearDown

    def testNew (self):
        filename = self.fileName()
        of = OpenOrCreate(filename)
        text = 'hello'
        texd = text.encode('utf-8')
        of.write(texd)
        of.close()

class TestOpenOrCreate_Local (unittest.TestCase, _TestOpenOrCreate_mixin):
    setUp = _TestOpenOrCreate_mixin.setUp
    tearDown = _TestOpenOrCreate_mixin.tearDown

    def testNew (self):
        filename = self.fileName()
        (path, localname) = os.path.split(filename)
        cwd = os.getcwd()
        try:
            os.chdir(path)
            of = OpenOrCreate(localname)
        finally:
            os.chdir(cwd)
        text = 'hello'
        texd = text.encode('utf-8')
        of.write(texd)
        of.close()

class TestOpenOrCreate_ExistingTagMatch (unittest.TestCase, _TestOpenOrCreate_mixin):
    setUp = _TestOpenOrCreate_mixin.setUp
    tearDown = _TestOpenOrCreate_mixin.tearDown

    def testExistingTagMatch (self):
        filename = self.fileName()
        tag = 'MyTagXX'
        text = 'This file has the tag %s in it' % (tag,)
        texd = text.encode('utf-8')
        fd = open(filename, 'wb')
        fd.write(texd)
        fd.close()
        fd = open(filename, 'rb')
        self.assertEqual(texd, fd.read())
        fd.close()
        of = OpenOrCreate(filename, tag=tag)
        text = 'New version with tag %s' % (tag,)
        texd = text.encode('utf-8')
        of.write(texd)
        of.close()
        fd = open(filename, 'rb')
        self.assertEqual(texd, fd.read())

class TestOpenOrCreate_ExistingTagMismatch (unittest.TestCase, _TestOpenOrCreate_mixin):
    setUp = _TestOpenOrCreate_mixin.setUp
    tearDown = _TestOpenOrCreate_mixin.tearDown

    def testExistingTagMismatch (self):
        filename = self.fileName()
        tag = 'MyTagXX'
        text = 'This file has the tag NotMyTag in it'
        texd = text.encode('utf-8')
        fd = open(filename, 'wb')
        fd.write(texd)
        fd.close()
        # Verify that opening for append will be positioned after the text.
        if 'win32' != sys.platform:
            fd = open(filename, 'a')
            self.assertTrue(0 < fd.tell())
            fd.close()
        fd = open(filename, 'rb')
        self.assertEqual(texd, fd.read())
        fd.close()
        if sys.version_info[:2] < (2, 7):
            self.assertRaises(OSError, OpenOrCreate, filename, tag=tag)
        else:
            with self.assertRaises(OSError) as cm:
                OpenOrCreate(filename, tag=tag)
            e = cm.exception
            self.assertEqual(e.errno, errno.EEXIST)

class TestHashForText (unittest.TestCase):

    def testBasic (self):
        text = 'This is some text'
        self.assertEqual('482cb0cfcbed6740a2bcb659c9ccc22a4d27b369', HashForText(text))

import datetime
class TestUTCTimeZone (unittest.TestCase):

    def testConstructors (self):
        dt = datetime.datetime.now()
        utc = UTCOffsetTimeZone()
        self.assertEqual(datetime.timedelta(0), utc.utcoffset(dt))
        self.assertEqual('Z', utc.tzname(dt))

        utc = UTCOffsetTimeZone('Z')
        self.assertEqual(datetime.timedelta(0), utc.utcoffset(dt))
        self.assertEqual('Z', utc.tzname(dt))

        utc = UTCOffsetTimeZone('+00:00')
        self.assertEqual(datetime.timedelta(0), utc.utcoffset(dt))
        self.assertEqual('Z', utc.tzname(dt))

        utc = UTCOffsetTimeZone('-00:00')
        self.assertEqual(datetime.timedelta(0), utc.utcoffset(dt))
        self.assertEqual('Z', utc.tzname(dt))

        utc = UTCOffsetTimeZone(95)
        self.assertEqual(datetime.timedelta(minutes=95), utc.utcoffset(dt))
        self.assertEqual('+01:35', utc.tzname(dt))

        td = datetime.timedelta(hours=3, minutes=42)
        utc = UTCOffsetTimeZone(td)
        self.assertEqual(td, utc.utcoffset(dt))
        self.assertEqual('+03:42', utc.tzname(dt))

    def testRangeValidation (self):
        dt = datetime.datetime.now()
        utc = UTCOffsetTimeZone('+13:59')
        self.assertEqual(datetime.timedelta(hours=13, minutes=59), utc.utcoffset(dt))
        self.assertEqual('+13:59', utc.tzname(dt))

        utc = UTCOffsetTimeZone('+14:00')
        self.assertEqual(datetime.timedelta(hours=14), utc.utcoffset(dt))
        self.assertEqual('+14:00', utc.tzname(dt))

        utc = UTCOffsetTimeZone('-13:59')
        self.assertEqual(-datetime.timedelta(hours=13, minutes=59), utc.utcoffset(dt))
        self.assertEqual('-13:59', utc.tzname(dt))

        utc = UTCOffsetTimeZone(-14*60)
        self.assertEqual(datetime.timedelta(hours=-14), utc.utcoffset(dt))
        self.assertEqual('-14:00', utc.tzname(dt))

        self.assertRaises(ValueError, UTCOffsetTimeZone, '14:01')
        self.assertRaises(ValueError, UTCOffsetTimeZone, -14*60 - 1)

    def testComparison (self):
        utc_a = UTCOffsetTimeZone()
        utc_b = UTCOffsetTimeZone('+00:00')
        utc_c = UTCOffsetTimeZone('-00:00')
        self.assertNotEqual(id(utc_a), id(utc_b))
        self.assertEqual(utc_a, utc_b)
        self.assertEqual(utc_a, utc_c)
        self.assertEqual(utc_b, utc_c)
        utc_p1 = UTCOffsetTimeZone(60)
        utc_m1 = UTCOffsetTimeZone(-60)
        self.assertTrue(utc_a < utc_p1)
        self.assertTrue(utc_m1 < utc_a)

class TestLocalTimeZone (unittest.TestCase):
    pass

class TestUniqueIdentifier (unittest.TestCase):

    def testBasic (self):
        u1 = UniqueIdentifier('one')
        self.assertEqual('one', u1.uid())
        u1b = UniqueIdentifier('one')
        self.assertEqual(u1, u1b)
        self.assertEqual(id(u1), id(u1b))

    def testNoUID (self):
        u1 = UniqueIdentifier()
        self.assertTrue(u1.uid() is not None)
        u2 = UniqueIdentifier(u1)
        self.assertEqual(id(u1), id(u2))

    def testPickling (self):
        import pickle
        import io

        u1 = UniqueIdentifier()
        outdata = io.BytesIO()
        pickler = pickle.Pickler(outdata, -1)
        pickler.dump(u1)
        instr = io.BytesIO(outdata.getvalue())
        unpickler = pickle.Unpickler(instr)
        u2 = unpickler.load()
        self.assertEqual(u1.uid(), u2.uid())
        self.assertEqual(u1, u2)
        self.assertEqual(id(u1), id(u2))

    def testStringEquivalence (self):
        u1 = UniqueIdentifier()
        self.assertEqual(u1, u1.uid())

    def testHash (self):
        u1 = UniqueIdentifier()
        mymap = { u1 : 'here' }
        self.assertTrue(u1 in mymap)
        self.assertTrue(u1.uid() in mymap)
        self.assertEqual('here', mymap[u1.uid()])

    def testStringize (self):
        u1 = UniqueIdentifier('one')
        self.assertEqual('one', str(u1))

    def testRepr (self):
        u1 = UniqueIdentifier()
        rep = repr(u1)
        self.assertEqual('pyxb.utils.utility.UniqueIdentifier(%s)' % (repr(u1.uid()),), repr(u1))
        import pyxb.utils.utility
        u1b = eval(repr(u1))
        self.assertEqual(id(u1), id(u1b))

import os
import re
class TestGetMatchingFiles (unittest.TestCase):
    __WXS_re = re.compile('\.wxs$')
    __NoExt_re = re.compile('(^|\%s)[^\.]+$' % os.sep)
    __directory = None
    def setUp (self):
        self.__directory = tempfile.mkdtemp()
        #print 'setup %s' % (self.__directory,)

        dir_hierarchy = [ 'd1', 'd2', 'd3', 'd1/d11', 'd1/d12', 'd1/d12/d121' ]
        [ os.mkdir(os.path.join(self.__directory, _d)) for _d in dir_hierarchy ]
        files = [ 'd1/f1a.wxs', 'd1/f1b.wxs', 'd1/f1c',
                  'd2/f2a.wxs', 'd2/f2b',
                  'd3/f3a.wxs',
                  'd1/d11/f11a.wxs', 'd1/d11/f11b.wxs',
                  'd1/d12/f12a.wxs', 'd1/d12/f12b',
                  'd1/d12/d121/f121a.wxs' ]
        [ open(os.path.join(self.__directory, _f), 'w') for _f in files ]

        self.__haveSymlink = hasattr(os, 'symlink')
        if self.__haveSymlink:
            os.symlink(os.path.join(self.__directory, 'd2'), os.path.join(self.__directory, 'd1', 'd11', 'l2'))

    def tearDown (self):
        #print 'teardown %s' % (self.__directory,)
        for (root, dirs, files) in os.walk(self.__directory, False):
            [ os.unlink(os.path.join(root, _f)) for _f in files ]
            for d in dirs:
                dp = os.path.join(root, d)
                try:
                    os.rmdir(dp)
                except OSError:
                    os.unlink(dp)
        os.rmdir(self.__directory)

    def _formPath (self, *args):
        out_args = []
        for a in args:
            if '+' == a:
                out_args.append(a)
            else:
                out_args.append(os.path.join(self.__directory, a))
        return os.pathsep.join(out_args)

    def _stripPath (self, files):
        return [ _f[len(self.__directory)+1:].replace(os.sep, '/') for _f in files ]

    def testFormPath (self):
        # Make sure _formPath preserves trailing slashes
        saved_dir = self.__directory
        candidates = [ 'a', 'a/', 'a//', '+' ]
        try:
            self.__directory = os.path.join(os.sep, 'test')
            expanded = self._formPath(*candidates)
            expected = os.pathsep.join([os.path.join(self.__directory, 'a'),
                                        os.path.join(self.__directory, 'a', ''),
                                        os.path.join(self.__directory, 'a//'),
                                        '+'])
            self.assertEqual(expected, expanded)
            candidates.pop()
            expanded = self._formPath(*candidates)
            condensed = self._stripPath(expanded.split(os.pathsep))
            self.assertEqual(candidates, condensed)
        finally:
            self.__directory = saved_dir

    def testD1 (self):
        files = set(self._stripPath(GetMatchingFiles(self._formPath('d1'))))
        self.assertEqual(files, set(['d1/f1c', 'd1/f1b.wxs', 'd1/f1a.wxs']))

    def testPattern (self):
        files = set(self._stripPath(GetMatchingFiles(self._formPath('d1'), self.__WXS_re)))
        self.assertEqual(files, set(['d1/f1b.wxs', 'd1/f1a.wxs']))
        files = set(self._stripPath(GetMatchingFiles(self._formPath('d1'), self.__NoExt_re)))
        self.assertEqual(files, set(['d1/f1c']))
        files = set(self._stripPath(GetMatchingFiles(self._formPath('d1', 'd2'), self.__WXS_re)))
        self.assertEqual(files, set(['d1/f1a.wxs', 'd1/f1b.wxs', 'd2/f2a.wxs']))

    def testD1D2 (self):
        files = set(self._stripPath(GetMatchingFiles(self._formPath('d1', 'd2'))))
        self.assertEqual(files, set(['d1/f1a.wxs', 'd1/f1b.wxs', 'd1/f1c', 'd2/f2a.wxs', 'd2/f2b']))

    def testLink (self):
        if self.__haveSymlink:
            files = set(self._stripPath(GetMatchingFiles(self._formPath(os.path.join('d1', 'd11', 'l2')))))
            self.assertEqual(files, set(['d1/d11/l2/f2a.wxs', 'd1/d11/l2/f2b']))

    def testDefault (self):
        kw = { 'default_path' : self._formPath('d1'),
               'default_path_wildcard' : '+' }
        files = set(self._stripPath(GetMatchingFiles(self._formPath('+'), self.__WXS_re, **kw)))
        self.assertEqual(files, set(['d1/f1b.wxs', 'd1/f1a.wxs']))
        files = set(self._stripPath(GetMatchingFiles(self._formPath('d2', '+'), self.__WXS_re, **kw)))
        self.assertEqual(files, set(['d1/f1a.wxs', 'd1/f1b.wxs', 'd2/f2a.wxs']))
        files = set(self._stripPath(GetMatchingFiles(self._formPath('+', 'd2'), self.__WXS_re, **kw)))
        self.assertEqual(files, set(['d1/f1a.wxs', 'd1/f1b.wxs', 'd2/f2a.wxs']))

    def testPrefixPattern (self):
        kw = { 'prefix_pattern' : '&',
               'prefix_substituend' : self.__directory }
        # Note: &/d1 => /d1 so it does not count
        files = set(self._stripPath(GetMatchingFiles(os.pathsep.join([os.path.join('&', 'd1'), '&d2']), self.__NoExt_re, **kw)))
        self.assertEqual(files, set(['d2/f2b']))

    def testRecursive (self):
        files = set(self._stripPath(GetMatchingFiles(self._formPath('d1//'), self.__WXS_re)))
        self.assertEqual(files, set(['d1/f1a.wxs', 'd1/f1b.wxs', 'd1/d11/f11a.wxs', 'd1/d12/f12a.wxs', 'd1/d11/f11b.wxs', 'd1/d12/d121/f121a.wxs']))

    def testFiles (self):
        files = set(self._stripPath(GetMatchingFiles(self._formPath('d1', os.path.join('d2', 'f2b')), self.__NoExt_re)))
        self.assertEqual(files, set(['d1/f1c', 'd2/f2b']))

class TestIteratedCompareMixed (unittest.TestCase):

    def testBasicSameLen (self):
        lhs = (1, 2, 3)
        self.assertEqual(0, IteratedCompareMixed(lhs, (1, 2, 3)))
        self.assertEqual(-1, IteratedCompareMixed(lhs, (2, 2, 4)))
        self.assertEqual(1, IteratedCompareMixed(lhs, (0, 2, 2)))
        self.assertEqual(-1, IteratedCompareMixed(lhs, (1, 2, 4)))
        self.assertEqual(1, IteratedCompareMixed(lhs, (1, 2, 2)))

    def testMixedSameLen (self):
        lhs = (1, 'two', 3.2)
        self.assertEqual(0, IteratedCompareMixed(lhs, (1, 'two', 3.2)))
        self.assertEqual(-1, IteratedCompareMixed(lhs, (2, 'two', 3.2)))
        self.assertEqual(-1, IteratedCompareMixed(lhs, (1, 'txo', 3.2)))
        self.assertEqual(-1, IteratedCompareMixed(lhs, (1, 'two', 3.3)))
        self.assertEqual(1, IteratedCompareMixed(lhs, (0, 'two', 3.2)))
        self.assertEqual(1, IteratedCompareMixed(lhs, (1, 'three', 3.2)))
        self.assertEqual(1, IteratedCompareMixed(lhs, (1, 'two', 3.1)))
        rhs = lhs
        self.assertEqual(0, IteratedCompareMixed((1, 'two', 3.2), rhs))
        self.assertEqual(1, IteratedCompareMixed((2, 'two', 3.2), rhs))
        self.assertEqual(1, IteratedCompareMixed((1, 'txo', 3.2), rhs))
        self.assertEqual(1, IteratedCompareMixed((1, 'two', 3.3), rhs))
        self.assertEqual(-1, IteratedCompareMixed((0, 'two', 3.2), rhs))
        self.assertEqual(-1, IteratedCompareMixed((1, 'three', 3.2), rhs))
        self.assertEqual(-1, IteratedCompareMixed((1, 'two', 3.1), rhs))

    def testMixedNoneSameLen (self):
        lhs = (1, 'two', 3.2)
        self.assertEqual(0, IteratedCompareMixed(lhs, (1, 'two', 3.2)))
        self.assertEqual(1, IteratedCompareMixed(lhs, (None, 'two', 3.2)))
        self.assertEqual(1, IteratedCompareMixed(lhs, (1, None, 3.2)))
        self.assertEqual(1, IteratedCompareMixed(lhs, (1, 'two', None)))
        rhs = (1, 'two', 3.2)
        self.assertEqual(-1, IteratedCompareMixed((None, 'two', 3.2), rhs))
        self.assertEqual(-1, IteratedCompareMixed((1, None, 3.2), rhs))
        self.assertEqual(-1, IteratedCompareMixed((1, 'two', None), rhs))

    def testDifferentLen (self):
        self.assertEqual(-1, IteratedCompareMixed((1, 2, 3), (1, 2, 3, -1)))
        self.assertEqual(1, IteratedCompareMixed((1, 2, 3, -1), (1, 2, 3)))

if '__main__' == __name__:
    unittest.main()
