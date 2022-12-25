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

"""This module contains support for processing XML using a SAX parser.

In particular, it provides a L{base content handler class<BaseSAXHandler>}
that maintains namespace context and element state in a stack; and a L{base
element state class <SAXElementState>} which records the location of the
element in the stream.  These classes are extended for specific parsing needs
(e.g., L{pyxb.binding.saxer}).
"""

from __future__ import print_function
import xml.sax
import xml.sax.handler
import io
import logging
import pyxb.namespace
from pyxb.utils import six

_log = logging.getLogger(__name__)

class TracingSAXHandler (xml.sax.handler.ContentHandler):
    """A SAX handler class which prints each method invocation.
    """

    # Whether invocation of handler methods should be traced
    __trace = False

    def setDocumentLocator (self, locator):
        print('setDocumentLocator %s' % (locator,))

    def startDocument (self):
        print('startDocument')

    def startPrefixMapping (self, prefix, uri):
        print('startPrefixMapping %s %s' % (prefix, uri))

    def endPrefixMapping (self, prefix):
        print('endPrefixMapping %s' % (prefix,))

    def startElementNS (self, name, qname, attrs):
        print('startElementNS %s %s' % (name, qname))

    def endElementNS (self, name, qname):
        print('endElementNS %s %s' % (name, qname))

    def characters (self, content):
        print('characters %s' % (content,))

    def ignorableWhitespace (self, whitespace):
        print('ignorableWhitespace len %d' % (len(whitespace),))

    def processingInstruction (self, target, data):
        print('processingInstruction %s %s' % (target, data))

class _NoopSAXHandler (xml.sax.handler.ContentHandler):
    """A SAX handler class which doesn't do anything.  Used to get baseline
    performance parsing a particular document.
    """

    def setDocumentLocator (self, locator):
        pass

    def startDocument (self):
        pass

    def startPrefixMapping (self, prefix, uri):
        pass

    def endPrefixMapping (self, prefix):
        pass

    def startElementNS (self, name, qname, attrs):
        pass

    def endElementNS (self, name, qname):
        pass

    def characters (self, content):
        pass

    def ignorableWhitespace (self, whitespace):
        pass

    def processingInstruction (self, target, data):
        pass

class SAXInformationItem (object):
    """Class used to capture an item discovered in the body of an element."""

    location = None
    """Where the item began in the document."""

    item = None
    """The item.  Generally either character information (as text) or a DOM
    Node instance or a binding instance."""

    maybe_element = None
    """C{False} iff the L{item} is character information as opposed to element content."""

    element_decl = None
    """A reference to the
    L{ElementDeclaration<pyxb.binding.content.ElementDeclaration>} used for
    the L{item}.  This will be C{None} for element content that does not have
    an enclosing CTD scope."""

    def __init__ (self, location, item, maybe_element, element_decl=None):
        self.location = location
        self.item = item
        self.maybe_element = maybe_element
        self.element_decl = element_decl

class SAXElementState (object):
    """State corresponding to processing a given element with the SAX
    model."""

    def contentHandler (self):
        """Reference to the C{xml.sxa.handler.ContentHandler} that is processing the document."""
        return self.__contentHandler
    __contentHandler = None

    def parentState (self):
        """Reference to the SAXElementState of the element enclosing this
        one."""
        return self.__parentState
    __parentState = None

    def namespaceContext (self):
        """The L{pyxb.namespace.NamespaceContext} used for this binding."""
        return self.__namespaceContext
    __namespaceContext = None

    def expandedName (self):
        """The L{expanded name<pyxb.namespace.ExpandedName>} of the
        element."""
        return self.__expandedName
    __expandedName = None

    def location (self):
        """The L{location<pyxb.utils.utility.Location>} corresponding to the
        element event."""
        return self.__location
    __location = None

    def content (self):
        """An accumulation of content to be supplied to the content model when
        the element end is reached.

        This is a list, with each member being C{(content, element_use,
        maybe_element)}.  C{content} is text or a binding instance;
        C{element_use} is C{None} or the
        L{ElementDeclaration<pyxb.binding.content.ElementDeclaration>} instance used to create
        the content; and C{maybe_element} is C{True} iff the content is
        non-content text."""
        return self.__content
    __content = None

    def __init__ (self, **kw):
        self.__expandedName = kw.get('expanded_name')
        self.__namespaceContext = kw['namespace_context']
        self.__parentState = kw.get('parent_state')
        self.__contentHandler = kw.get('content_handler')
        assert self.__contentHandler is not None
        self.__location = self.__contentHandler.location()
        self.__content = []

    def addTextContent (self, location, content):
        """Add the given text as non-element content of the current element.
        @type content: C{unicode} or C{str}
        @return: C{self}
        """
        self.__content.append(SAXInformationItem(location, content, False))

    def addElementContent (self, location, element, element_decl=None):
        """Add the given binding instance as element content corresponding to
        the given use.

        @param element: Any L{binding instance<pyxb.binding.basis._TypeBinding_mixin>}.

        @param element_decl: The L{element
        use<pyxb.binding.content.ElementDeclaration>} in the containing complex type.
        """
        self.__content.append(SAXInformationItem(location, element, True, element_decl))

class BaseSAXHandler (xml.sax.handler.ContentHandler, object):
    """A SAX handler class that maintains a stack of enclosing elements and
    manages namespace declarations.

    This is the base for L{pyxb.utils.saxdom._DOMSAXHandler} and
    L{pyxb.binding.saxer.PyXBSAXHandler}.
    """

    # An instance of L{pyxb.utils.utility.Location} that will be used to
    # construct the locations of events as they are received.
    __locationTemplate = None

    def location (self):
        """Return the current location within the SAX-processed document."""
        return self.__locationTemplate.newLocation(self.__locator)

    # The callable that creates an instance of (a subclass of)
    # L{SAXElementState} as required to hold element-specific information as
    # parsing proceeds.
    __elementStateConstructor = None

    # The namespace to use when processing a document with an absent default
    # namespace.
    def fallbackNamespace (self):
        """Return the namespace used to resolve unqualified names with no default namespace."""
        return self.__fallbackNamespace
    __fallbackNamespace = None

    # The namespace context that will be in effect at the start of the next
    # element, or C{None} if no namespace directive notifications have been
    # received since the last element start or end.  Namespace directive
    # notifications are received before the notification of element start in
    # which they apply, and cause a "next namespace context" to be allocated
    # referencing the current namespace.  The directive is applied to the next
    # context.  A non-None next context becomes active on entry to the next
    # element.  The next context is reset to None on entry to and exit from an
    # element so subsequent new directives are applied to a fresh context
    # inherited from the current context.
    __nextNamespaceContext = None

    # The namespace context that is in effect for this element.
    def namespaceContext (self):
        """Return the namespace context used for QName resolution within the
        current element.

        @return: An instance of L{pyxb.namespace.NamespaceContext}"""
        return self.__namespaceContext
    __namespaceContext = None

    # The namespace context in a schema that is including the schema to be
    # parsed by this handler.  This is necessary to handle section 4.2.1 when
    # a schema with a non-absent target namespace includes a schema with no
    # target namespace.
    __includingContext = None

    # A SAX locator object.  @todo: Figure out how to associate the
    # location information with the binding objects.
    __locator = None

    # The state for the element currently being processed
    def elementState (self):
        return self.__elementState
    __elementState = None

    # The states for all enclosing elements
    __elementStateStack = []

    def rootObject (self):
        """Return the binding object corresponding to the top-most
        element in the document

        @return: An instance of L{basis._TypeBinding_mixin} (most usually a
        L{basis.complexTypeDefinition}."""
        return self.__rootObject
    __rootObject = None

    def reset (self):
        """Reset the state of the handler in preparation for processing a new
        document.

        @return: C{self}
        """
        self.__namespaceContext = pyxb.namespace.NamespaceContext(default_namespace=self.__fallbackNamespace,
                                                                  target_namespace=self.__targetNamespace,
                                                                  including_context=self.__includingContext,
                                                                  finalize_target_namespace=False)
        self.__nextNamespaceContext = None
        self.__elementState = self.__elementStateConstructor(content_handler=self,
                                                             namespace_context=self.__namespaceContext)
        self.__elementStateStack = []
        self.__rootObject = None
        # Note: setDocumentLocator is invoked before startDocument (which
        # calls this), so this method should not reset it.
        return self

    def __init__ (self, **kw):
        """Create a new C{xml.sax.handler.ContentHandler} instance to maintain state relevant to elements.

        @keyword fallback_namespace: Optional namespace to use for unqualified
        names with no default namespace in scope.  Has no effect unless it is
        an absent namespace.

        @keyword element_state_constructor: Optional callable object that
        creates instances of L{SAXElementState} that hold element-specific
        information.  Defaults to L{SAXElementState}.

        @keyword target_namespace: Optional namespace to set as the target
        namespace.  If not provided, there is no target namespace (not even an
        absent one).  This is the appropriate situation when processing plain
        XML documents.

        @keyword location_base: An object to be recorded as the base of all
        L{pyxb.utils.utility.Location} instances associated with events and
        objects handled by the parser.
        """
        self.__includingContext = kw.pop('including_context', None)
        self.__fallbackNamespace = kw.pop('fallback_namespace', None)
        self.__elementStateConstructor = kw.pop('element_state_constructor', SAXElementState)
        self.__targetNamespace = kw.pop('target_namespace', None)
        self.__locationTemplate = pyxb.utils.utility.Location(kw.pop('location_base', None))

    def setDocumentLocator (self, locator):
        """Save the locator object."""
        self.__locator = locator

    def startDocument (self):
        """Process the start of a document.

        This resets this handler for a new document.
        @note: setDocumentLocator is invoked before startDocument
        """
        self.reset()

    def __getOrCreateNextNamespaceContext (self):
        ns_ctx = self.__nextNamespaceContext
        if ns_ctx is None:
            assert self.__namespaceContext is not None
            ns_ctx = pyxb.namespace.NamespaceContext(parent_context=self.__namespaceContext)
            self.__nextNamespaceContext = ns_ctx
        return ns_ctx

    def startPrefixMapping (self, prefix, uri):
        """Implement base class method.

        @note: For this to be invoked, the C{feature_namespaces} feature must
        be enabled in the SAX parser."""
        self.__getOrCreateNextNamespaceContext().processXMLNS(prefix, uri)

    # The NamespaceContext management does not require any action upon
    # leaving the scope of a namespace directive.
    #def endPrefixMapping (self, prefix):
    #    pass

    def startElementNS (self, name, qname, attrs):
        """Process the start of an element."""
        self.__flushPendingText()

        # Get the element name, which is already a tuple with the namespace assigned.
        expanded_name = pyxb.namespace.ExpandedName(name, fallback_namespace=self.__fallbackNamespace)

        # See if this element supports a targetNamespace attribute.  xs:schema
        # and wsdl:definitions both do.
        tns_attr = pyxb.namespace.NamespaceContext._TargetNamespaceAttribute(expanded_name)

        # If we need to assign a target namespace, we need a new context.
        # Otherwise we use the context created from pending namespace
        # directives, or we re-use the current context.
        if tns_attr is not None:
            ns_ctx = self.__getOrCreateNextNamespaceContext()
        else:
            ns_ctx = self.__nextNamespaceContext
        if ns_ctx is None:
            # Re-use the active context
            ns_ctx = self.__namespaceContext
        else:
            # Update the active context
            self.__namespaceContext = ns_ctx
        self.__nextNamespaceContext = None

        if tns_attr is not None:
            # Not true for wsdl
            #assert ns_ctx.targetNamespace() is None
            ns_ctx.finalizeTargetNamespace(attrs.get(tns_attr.uriTuple()), including_context=self.__includingContext)
            assert ns_ctx.targetNamespace() is not None

        # Save the state of the enclosing element, and create a new
        # state for this element.
        parent_state = self.__elementState
        self.__elementStateStack.append(self.__elementState)
        self.__elementState = this_state = self.__elementStateConstructor(content_handler=self,
                                                                          expanded_name=expanded_name,
                                                                          namespace_context=ns_ctx,
                                                                          parent_state=parent_state)
        return (this_state, parent_state, ns_ctx, expanded_name)

    def endElementNS (self, name, qname):
        """Process the completion of an element."""
        self.__flushPendingText()

        # Save the state of this element, and restore the state for
        # the parent to which we are returning.
        this_state = self.__elementState
        parent_state = self.__elementState = self.__elementStateStack.pop()
        # Restore namespace context and prepare for new namespace directives
        self.__namespaceContext = parent_state.namespaceContext()
        self.__nextNamespaceContext = None

        return this_state

    # We accumulate consecutive text events into a single event, primarily to
    # avoid the confusion that results when the value of a simple type is
    # represented by multiple events, as with "B &amp; W".  Also, it's faster
    # to join them all at once, and to process one content value rather than a
    # sequence of them.
    __pendingText = None
    __pendingTextLocation = None
    def __flushPendingText (self):
        if self.__pendingText:
            location = self.__pendingTextLocation
            if location is None:
                location = self.location()
            self.__elementState.addTextContent(location, ''.join(self.__pendingText))
        self.__pendingTextLocation = None
        self.__pendingText = []

    def characters (self, content):
        """Save the text as content"""
        if self.__pendingTextLocation is None:
            self.__pendingTextLocation = self.location()
        self.__pendingText.append(content)

    def ignorableWhitespace (self, whitespace):
        """Save whitespace as content too."""
        self.__pendingText.append(whitespace)

    def processingInstruction (self, target, data):
        self.__flushPendingText()

class _EntityResolver (object):
    """Dummy used to prevent the SAX parser from crashing when it sees
    processing instructions that we don't care about."""
    def resolveEntity (self, public_id, system_id):
        return io.StringIO(six.u(''))

_CreateParserModules = []
def SetCreateParserModules (create_parser_modules):
    """Provide list of modules to be used when creating parsers.

    C{xml.sax.make_parser()} takes as a parameter an optional list of modules
    which allow customization of the parser to be used.  Certain parsers have
    better support for Unicode than others.

    As an example, providing C{["drv_libxml2"]} causes the libxml2 parser to
    be used.

    The default behavior if this function is not called, or if it is called
    with an empty list or C{None}, is to provide no specific modules, which
    will result in the system default parser (probably expat).

    @param create_parser_modules: an iterable list of names of modules that
    provide a C{create_parser} function.  Pass C{None} to reset to the system
    default.  """
    global _CreateParserModules
    if create_parser_modules is None:
        _CreateParserModules = []
    else:
        _CreateParserModules = list(create_parser_modules)

def make_parser (**kw):
    """Extend C{xml.sax.make_parser} to configure the parser the way we
    need it:

      - C{feature_namespaces} is set to C{True} so we process xmlns
        directives properly
      - C{feature_namespace_prefixes} is set to C{False} so we don't get
        prefixes encoded into our names (probably redundant with the above but
        still...)

    All keywords not documented here (and C{fallback_namespace}, which is) are
    passed to the C{content_handler_constructor} if that must be invoked.

    @keyword content_handler: The content handler instance for the
    parser to use.  If not provided, an instance of C{content_handler_constructor}
    is created and used.
    @type content_handler: C{xml.sax.handler.ContentHandler}

    @keyword content_handler_constructor: A callable which produces an
    appropriate instance of (a subclass of) L{BaseSAXHandler}.  The default is
    L{BaseSAXHandler}.

    @keyword fallback_namespace: The namespace to use for lookups of
    unqualified names in absent namespaces; see
    L{pyxb.namespace.ExpandedName}.  This keyword is not used by this
    function, but is passed to the C{content_handler_constructor}.
    @type fallback_namespace: L{pyxb.namespace.Namespace}
    """
    content_handler_constructor = kw.pop('content_handler_constructor', BaseSAXHandler)
    content_handler = kw.pop('content_handler', None)
    if content_handler is None:
        content_handler = content_handler_constructor(**kw)
    parser = xml.sax.make_parser(_CreateParserModules)
    parser.setFeature(xml.sax.handler.feature_namespaces, True)
    parser.setFeature(xml.sax.handler.feature_namespace_prefixes, False)
    parser.setContentHandler(content_handler)
    # libxml2 doesn't support this feature
    try:
        parser.setEntityResolver(_EntityResolver())
    except xml.sax.SAXNotSupportedException:
        pass
    return parser

if '__main__' == __name__:
    import xml.dom.pulldom
    import xml.dom.minidom
    import pyxb.utils.saxdom as saxdom
    import time
    import lxml.sax
    import lxml.etree
    import sys

    Handler = BaseSAXHandler
    xml_file = 'examples/tmsxtvd/tmsdatadirect_sample.xml'
    if 1 < len(sys.argv):
        xml_file = sys.argv[1]
    xmld = open(xml_file, 'rb').read()

    dt1 = time.time()
    dt2 = time.time()
    dom = xml.dom.minidom.parse(io.BytesIO(xmld))
    dt3 = time.time()

    snt1 = time.time()
    saxer = make_parser(content_handler=_NoopSAXHandler())
    snt2 = time.time()
    saxer.parse(io.BytesIO(xmld))
    snt3 = time.time()

    sbt1 = time.time()
    saxer = make_parser(content_handler=BaseSAXHandler())
    sbt2 = time.time()
    saxer.parse(io.BytesIO(xmld))
    sbt3 = time.time()

    pdt1 = time.time()
    sdomer = make_parser(content_handler_constructor=saxdom._DOMSAXHandler)
    h = sdomer.getContentHandler()
    pdt2 = time.time()
    sdomer.parse(io.BytesIO(xmld))
    pdt3 = time.time()

    lst1 = time.time()
    tree = lxml.etree.fromstring(xmld)
    lst2 = time.time()
    lsh = Handler()
    lxml.sax.saxify(tree, lsh)
    lst3 = time.time()

    ldt1 = time.time()
    tree = lxml.etree.fromstring(xmld)
    ldt2 = time.time()
    ldh = xml.dom.pulldom.SAX2DOM()
    lxml.sax.saxify(tree, ldh)
    ldt3 = time.time()

    print('minidom read %f, parse %f, total %f' % (dt2-dt1, dt3-dt2, dt3-dt1))
    print('SAX+noop create %f, parse %f, total %f' % (snt2-snt1, snt3-snt2, snt3-snt1))
    print('SAX+ns create %f, parse %f, total %f' % (sbt2-sbt1, sbt3-sbt2, sbt3-sbt1))
    print('PyXB SAXDOM-based create %f, parse %f, total %f' % (pdt2-pdt1, pdt3-pdt2, pdt3-pdt1))
    print('LXML+SAX tree %f, parse %f, total %f' % (lst2-lst1, lst3-lst2, lst3-lst1))
    print('LXML+pulldom DOM tree %f, parse %f, total %f' % (ldt2-ldt1, ldt3-ldt2, ldt3-ldt1))

## Local Variables:
## fill-column:78
## End:
