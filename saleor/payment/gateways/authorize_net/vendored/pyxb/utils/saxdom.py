# -*- coding: utf-8 -*-
# Copyright 2009-2013, Peter A. Bigot
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain a
# copy of the License at:
#
#            http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""This module contains support for a DOM tree representation from an XML
document using a SAX parser.

This functionality exists because we need a DOM interface to generate the
binding classses, but the Python C{xml.dom.minidom} package does not support
location information.  The SAX interface does, so we have a SAX content
handler which converts the SAX events into a DOM tree.

This is not a general-purpose DOM capability; only a small subset of the DOM
interface is supported, and only for storing the XML information, not for
converting it back into document format.
"""

from __future__ import print_function
import logging
import io
import xml.dom
import pyxb.utils.saxutils
from pyxb.utils import six
import pyxb.namespace

_log = logging.getLogger(__name__)

def _DumpDOM (n, depth=0):
    """Utility function to print a DOM tree."""

    pfx = ' ' * depth
    if (xml.dom.Node.ELEMENT_NODE == n.nodeType):
        print('%sElement[%d] %s %s with %d children' % (pfx, n._indexInParent(), n, pyxb.namespace.ExpandedName(n.name), len(n.childNodes)))
        ins = pyxb.namespace.NamespaceContext.GetNodeContext(n).inScopeNamespaces()
        print('%s%s' % (pfx, ' ; '.join([ '%s=%s' % (_k, _v.uri()) for (_k, _v) in ins.items()])))
        for (k, v) in six.iteritems(n.attributes):
            print('%s %s=%s' % (pfx, pyxb.namespace.ExpandedName(k), v))
        for cn in n.childNodes:
            _DumpDOM(cn, depth+1)
    elif (xml.dom.Node.TEXT_NODE == n.nodeType):
        #print '%sText "%s"' % (pfx, n.value)
        pass
    elif (xml.dom.Node.DOCUMENT_NODE == n.nodeType):
        print('Document node')
        _DumpDOM(n.firstChild, depth)
    else:
        print('UNRECOGNIZED %s' % (n.nodeType,))

class _DOMSAXHandler (pyxb.utils.saxutils.BaseSAXHandler):
    """SAX handler class that transforms events into a DOM tree."""

    def document (self):
        """The document that is the root of the generated tree."""
        return self.__document
    __document = None

    def startDocument (self):
        super(_DOMSAXHandler, self).startDocument()
        self.__document = Document(namespace_context=self.namespaceContext())

    def endDocument (self):
        content = self.elementState().content()
        if 0 < len(content):
            assert content[0].maybe_element
            self.__document.appendChild(content[0].item)
            #_DumpDOM(content)

    def startElementNS (self, name, qname, attrs):
        (this_state, parent_state, ns_ctx, name_en) = super(_DOMSAXHandler, self).startElementNS(name, qname, attrs)
        this_state.__attributes = NamedNodeMap()
        for name in attrs.getNames():
            attr_en = pyxb.namespace.ExpandedName(name)
            value = attrs.getValue(name)
            this_state.__attributes._addItem(Attr(expanded_name=attr_en, namespace_context=ns_ctx, value=value, location=this_state.location()))

    def endElementNS (self, name, qname):
        this_state = super(_DOMSAXHandler, self).endElementNS(name, qname)
        ns_ctx = this_state.namespaceContext()
        element = Element(namespace_context=ns_ctx, expanded_name=this_state.expandedName(), attributes=this_state.__attributes, location=this_state.location())
        for info in this_state.content():
            if isinstance(info.item, Node):
                element.appendChild(info.item)
            else:
                element.appendChild(Text(info.item, namespace_context=ns_ctx))
        parent_state = this_state.parentState()
        parent_state.addElementContent(this_state.location(), element, None)

def parse (stream, **kw):
    """Parse a stream containing an XML document and return the DOM tree
    representing its contents.

    Keywords not described here are passed to L{pyxb.utils.saxutils.make_parser}.

    @param stream: An object presenting the standard file C{read} interface
    from which the document can be read.  The content should be data, not text.

    @keyword content_handler_constructor: Input is overridden to assign this a
    value of L{_DOMSAXHandler}.

    @rtype: C{xml.dom.Document}
    """

    kw['content_handler_constructor'] = _DOMSAXHandler
    saxer = pyxb.utils.saxutils.make_parser(**kw)
    handler = saxer.getContentHandler()
    saxer.parse(stream)
    return handler.document()

def parseString (xml_text, **kw):
    """Parse a string holding an XML document and return the corresponding DOM
    tree.

    @param xml_text: the XML content to be parsed, in a text representation."""
    # SAX parser operates on data, not text.
    xmld = xml_text
    if isinstance(xmld, six.text_type):
        xmld = xmld.encode(pyxb._InputEncoding)
    return parse(io.BytesIO(xmld), **kw)

class Node (xml.dom.Node, pyxb.utils.utility.Locatable_mixin):
    """Base for the minimal DOM interface required by PyXB."""
    def __init__ (self, node_type, **kw):
        location = kw.pop('location', None)
        if location is not None:
            pyxb.utils.utility.Locatable_mixin.__init__(self, location=location)
        self.__nodeType = node_type
        self.__parentNode = None
        self.__indexInParent = None
        self.__childNodes = []
        self.__namespaceContext = kw['namespace_context']
        self.__value = kw.get('value')
        self.__attributes = kw.get('attributes')
        en = kw.get('expanded_name')
        if en is not None:
            self.__expandedName = en
            ns = en.namespace()
            if (ns is not None) and not (ns.prefix() is None):
                assert not ns.isAbsentNamespace()
                self.__prefix = ns.prefix()
            if (ns is not None):
                self.__namespaceURI = ns.uri()
            self.__localName = en.localName()
            if self.__prefix:
                self.__tagName = '%s:%s' % (self.__prefix, self.__localName)
            else:
                self.__tagName = self.__localName
        self.__namespaceContext.setNodeContext(self)

    location = property(lambda _s: _s._location())

    __expandedName = None
    _expandedName = property(lambda _s: _s.__expandedName)
    __prefix = ''
    prefix = property(lambda _s: _s.__prefix)
    __tagName = ''
    tagName = property(lambda _s: _s.__tagName)
    __namespaceURI = None
    namespaceURI = property(lambda _s: _s.__namespaceURI)
    __localName = None
    localName = property(lambda _s: _s.__localName)
    __value = None
    value = property(lambda _s: _s.__value)

    def _indexInParent (self): return self.__indexInParent

    def __childIfPresent (self, index):
        if index < len(self.__childNodes):
            return self.__childNodes[index]
        return None

    def appendChild (self, new_child):
        new_child._setParentNode(self, len(self.__childNodes))
        self.__childNodes.append(new_child)

    def _setParentNode (self, parent_node, index_in_parent):
        self.__parentNode = parent_node
        self.__indexInParent = index_in_parent

    def _setAttributes (self, attributes):
        assert self.__attributes is None
        self.__attributes = attributes
    __attributes = None

    nodeType = property(lambda _s: _s.__nodeType)
    parentNode = property(lambda _s: _s.__parentNode)
    firstChild = property(lambda _s: _s.__childIfPresent(0))
    childNodes = property(lambda _s: _s.__childNodes)
    attributes = property(lambda _s: _s.__attributes)

    nextSibling = property(lambda _s: _s.parentNode.__childIfPresent(_s.__indexInParent+1))

    def hasAttributeNS (self, ns_uri, local_name):
        return self.getAttributeNodeNS(ns_uri, local_name) is not None

    def getAttributeNodeNS (self, ns_uri, local_name):
        return self.__attributes._getAttr(pyxb.namespace.ExpandedName(ns_uri, local_name))

    def getAttributeNS (self, ns_uri, local_name):
        rv = self.getAttributeNodeNS(ns_uri, local_name)
        if rv is None:
            return ''
        return rv.value

class Document (Node):
    """Add the documentElement interface."""
    def __init__ (self, **kw):
        super(Document, self).__init__(node_type=xml.dom.Node.DOCUMENT_NODE, **kw)

    documentElement = Node.firstChild

class Attr (Node):
    """Add the nodeName and nodeValue interface."""
    def __init__ (self, **kw):
        super(Attr, self).__init__(node_type=xml.dom.Node.ATTRIBUTE_NODE, **kw)
    name = Node.tagName
    nodeName = Node.tagName
    nodeValue = Node.value

class NamedNodeMap (object):
    """Implement that portion of NamedNodeMap required to satisfy PyXB's
    needs."""
    __members = None
    __memberMap = None

    def __init__ (self):
        super(NamedNodeMap, self).__init__()
        self.__members = []
        self.__memberMap = {}

    length = property(lambda _s: len(_s.__members))
    def item (self, index):
        return self.__members[index]

    def _addItem (self, attr):
        assert pyxb.namespace.NamespaceContext.GetNodeContext(attr) is not None
        self.__members.append(attr)
        en = attr._expandedName
        if en is not None:
            self.__memberMap[en] = attr

    def _getAttr (self, name):
        rv = self.__memberMap.get(name)
        if rv is not None:
            return rv
        return None

class Element (Node):
    def __init__ (self, **kw):
        super(Element, self).__init__(node_type=xml.dom.Node.ELEMENT_NODE, **kw)
        assert self.attributes is not None
    tagName = Node.localName
    nodeName = Node.localName

class _CharacterData (Node):
    """Abstract base for anything holding text data."""
    data = Node.value

class Text (_CharacterData):
    def __init__ (self, text, **kw):
        super(Text, self).__init__(value=text, node_type=xml.dom.Node.TEXT_NODE, **kw)

class Comment (_CharacterData):
    def __init__ (self, text, **kw):
        super(Comment, self).__init__(value=text, node_type=xml.dom.Node.COMMENT_NODE, **kw)

if '__main__' == __name__:
    import sys
    xml_file = 'examples/tmsxtvd/tmsdatadirect_sample.xml'
    if 1 < len(sys.argv):
        xml_file = sys.argv[1]

    doc = parse(open(xml_file))

## Local Variables:
## fill-column:78
## End:
