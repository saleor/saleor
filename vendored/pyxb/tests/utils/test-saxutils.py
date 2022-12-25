# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import unittest
from pyxb.utils.saxutils import *
from xml.dom import Node
import xml.dom
import pyxb.namespace

class TestState (SAXElementState):
    StateSequence = []

    def __init__ (self, *args, **kw):
        self.StateSequence.append(self)
        super(TestState, self).__init__(*args, **kw)

BogusNamespace = pyxb.namespace.NamespaceInstance('urn:test-saxutils-bogus')
books_ns = pyxb.namespace.NamespaceInstance('urn:loc.gov:books')
isbn_ns = pyxb.namespace.NamespaceInstance('urn:ISBN:0-395-36341-6')
xhtml_ns = pyxb.namespace.NamespaceInstance('http://www.w3.org/1999/xhtml')

class TestInScopeNames (unittest.TestCase):
    def show (self, node):
        xmlns_map = pyxb.namespace.NamespaceContext.GetNodeContext(node).inScopeNamespaces()
        #print '%s: %s' % (node.nodeName, ' ; '.join([ '%s=%s' % (_k, _v.uri()) for (_k, _v) in six.iteritems(xmlns_map)]))
        return xmlns_map

    def tearDown (self):
        TestState.StateSequence[:] = []

    def stripUndeclaredNamespaces (self, xmlns_map):
        xmlns_map = xmlns_map.copy()
        self.assertEqual(pyxb.namespace.XML.uri(), xmlns_map.pop('xml').uri())
        self.assertEqual(pyxb.namespace.XMLNamespaces.uri(), xmlns_map.pop('xmlns').uri())
        return xmlns_map

    def test_6_2_2 (self):
        xmld = '''<?xml version="1.0"?>
<!-- initially, the default namespace is "books" -->
<book xmlns='urn:loc.gov:books'
      xmlns:isbn='urn:ISBN:0-395-36341-6'>
    <title>Cheaper by the Dozen</title>
    <isbn:number>1568491379</isbn:number>
    <notes>
      <p xmlns='http://www.w3.org/1999/xhtml'>
          This is a <i>funny</i> book!
      </p>
      <p>another graf without namespace change</p>
    </notes>
</book>'''.encode('utf-8')
        saxer = make_parser(element_state_constructor=TestState, location_base='test_6_2_2', fallback_namespace=BogusNamespace)
        handler = saxer.getContentHandler()
        saxer.parse(io.BytesIO(xmld))

        # First is root context; second is the book element
        book = TestState.StateSequence[1]
        en = book.expandedName()
        self.assertTrue(en is not None)
        self.assertEqual(en.namespace(), books_ns)
        self.assertEqual(en.localName(), 'book')
        self.assertEqual(book.namespaceContext().defaultNamespace(), books_ns)
        self.assertEqual(book.namespaceContext().inScopeNamespaces().get('isbn'), isbn_ns)

        title = TestState.StateSequence[2]
        xmlns_map = self.stripUndeclaredNamespaces(title.namespaceContext().inScopeNamespaces())
        self.assertEqual(2, len(xmlns_map))
        self.assertEqual('urn:loc.gov:books', xmlns_map[None].uri())
        self.assertEqual('urn:ISBN:0-395-36341-6', xmlns_map['isbn'].uri())

        p = TestState.StateSequence[5]
        xmlns_map = self.stripUndeclaredNamespaces(p.namespaceContext().inScopeNamespaces())
        self.assertEqual(p.expandedName().localName(), 'p')
        self.assertEqual(2, len(xmlns_map))
        self.assertEqual('http://www.w3.org/1999/xhtml', xmlns_map[None].uri())
        self.assertEqual('urn:ISBN:0-395-36341-6', xmlns_map['isbn'].uri())

        x = TestState.StateSequence[7]
        xmlns_map = self.stripUndeclaredNamespaces(x.namespaceContext().inScopeNamespaces())
        self.assertEqual(x.expandedName().localName(), 'p')
        self.assertEqual(2, len(xmlns_map))
        self.assertEqual('urn:loc.gov:books', xmlns_map[None].uri())
        self.assertEqual('urn:ISBN:0-395-36341-6', xmlns_map['isbn'].uri())

    def test_6_2_3 (self):
        xmld = '''<?xml version='1.0'?>
<Beers>
  <table xmlns='http://www.w3.org/1999/xhtml'>
   <th><td>Name</td><td>Origin</td><td>Description</td></th>
   <tr>
     <td><brandName xmlns="">Huntsman</brandName></td>
     <td><origin xmlns="">Bath, UK</origin></td>
     <td>
       <details xmlns=""><class>Bitter</class><hop>Fuggles</hop>
         <pro>Wonderful hop, light alcohol, good summer beer</pro>
         <con>Fragile; excessive variance pub to pub</con>
         </details>
        </td>
      </tr>
    </table>
  </Beers>'''.encode('utf-8')

        saxer = make_parser(element_state_constructor=TestState, location_base='test_6_2_3', fallback_namespace=BogusNamespace)
        handler = saxer.getContentHandler()
        saxer.parse(io.BytesIO(xmld))

        Beers = TestState.StateSequence[1]
        xmlns_map = self.stripUndeclaredNamespaces(Beers.namespaceContext().inScopeNamespaces())
        self.assertEqual(0, len(xmlns_map))
        table = TestState.StateSequence[2]
        self.assertEqual(xhtml_ns.createExpandedName('table'), table.expandedName())
        xmlns_map = self.stripUndeclaredNamespaces(table.namespaceContext().inScopeNamespaces())
        self.assertEqual(1, len(xmlns_map))
        self.assertEqual('http://www.w3.org/1999/xhtml', xmlns_map[None].uri())
        brandName = TestState.StateSequence[9]
        xmlns_map = self.stripUndeclaredNamespaces(brandName.namespaceContext().inScopeNamespaces())
        self.assertTrue(brandName.expandedName().namespace() is None)
        self.assertEqual('brandName', brandName.expandedName().localName())
        self.assertEqual(0, len(xmlns_map))

if '__main__' == __name__:
    unittest.main()
