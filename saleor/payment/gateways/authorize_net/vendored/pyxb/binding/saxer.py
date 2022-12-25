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

"""This module contains support for generating bindings from an XML stream
using a SAX parser."""

import logging
import xml.dom
import pyxb.namespace
import pyxb.utils.saxutils
import pyxb.utils.saxdom
import pyxb.utils.utility
from pyxb.binding import basis
from pyxb.namespace.builtin import XMLSchema_instance as XSI

_log = logging.getLogger(__name__)

class _SAXElementState (pyxb.utils.saxutils.SAXElementState):
    """State required to generate bindings for a specific element.

    If the document being parsed includes references to unrecognized elements,
    a DOM instance of the element and its content is created and treated as a
    wildcard element.
    """

    # An expanded name corresponding to xsi:nil
    __XSINilTuple = XSI.nil.uriTuple()

    # The binding instance being created for this element.  When the
    # element type has simple content, the binding instance cannot be
    # created until the end of the element has been reached and the
    # content of the element has been processed accumulated for use in
    # the instance constructor.  When the element type has complex
    # content, the binding instance must be created at the start of
    # the element, so contained elements can be properly stored.
    __bindingInstance = None

    # The schema binding for the element being constructed.
    __elementBinding = None

    def setElementBinding (self, element_binding):
        """Record the binding to be used for this element.

        Generally ignored, except at the top level this is the only way to
        associate a binding instance created from an xsi:type description with
        a specific element."""
        self.__elementBinding = element_binding

    # The nearest enclosing complex type definition
    def enclosingCTD (self):
        """The nearest enclosing complex type definition, as used for
        resolving local element/attribute names.

        @return: An instance of L{basis.complexTypeDefinition}, or C{None} if
        the element is top-level
        """
        return self.__enclosingCTD
    __enclosingCTD = None

    # The factory that is called to create a binding instance for this
    # element; None if the binding instance was created at the start
    # of the element.
    __delayedConstructor = None

    # An xml.sax.xmlreader.Attributes instance providing the
    # attributes for the element.
    __attributes = None

    # An xml.dom.Node corresponding to the (sub-)document
    __domDocument = None

    __domDepth = None

    def __init__ (self, **kw):
        super(_SAXElementState, self).__init__(**kw)
        self.__bindingInstance = None
        parent_state = self.parentState()
        if isinstance(parent_state, _SAXElementState):
            self.__enclosingCTD = parent_state.enclosingCTD()
            self.__domDocument = parent_state.__domDocument
            if self.__domDocument is not None:
                self.__domDepth = parent_state.__domDepth + 1

    def setEnclosingCTD (self, enclosing_ctd):
        """Set the enclosing complex type definition for this element.

        @param enclosing_ctd: The scope for a local element.
        @type enclosing_ctd: L{basis.complexTypeDefinition}
        @return: C{self}
        """
        self.__enclosingCTD = enclosing_ctd

    # Create the binding instance for this element.
    def __constructElement (self, new_object_factory, attrs, content=None):
        kw = { '_from_xml' : True,
               '_location' : self.location() }

        # Note whether the node is marked nil
        if self.__XSINilTuple in attrs:
            kw['_nil'] = pyxb.binding.datatypes.boolean(attrs.getValue(self.__XSINilTuple))

        if content is None:
            content = []
        self.__bindingInstance = new_object_factory(*content, **kw)
        if isinstance(self.__bindingInstance, pyxb.utils.utility.Locatable_mixin):
            self.__bindingInstance._setLocation(self.location())

        # Record the namespace context so users of the binding can
        # interpret QNames within the attributes and content.
        self.__bindingInstance._setNamespaceContext(self.__namespaceContext)

        # Set instance attributes
        # NB: attrs implements the SAX AttributesNS interface, meaning
        # that names are pairs of (namespaceURI, localName), just like we
        # want them to be.
        for attr_name in self.__attributes.getNames():
            attr_en = pyxb.namespace.ExpandedName(attr_name)
            # Ignore xmlns and xsi attributes; we've already handled those
            if attr_en.namespace() in ( pyxb.namespace.XMLNamespaces, XSI ):
                continue
            # The binding instance may be a simple type that does not support
            # attributes; the following raises an exception in that case.
            self.__bindingInstance._setAttribute(attr_en, attrs.getValue(attr_name))

        return self.__bindingInstance

    def inDOMMode (self):
        return self.__domDocument is not None

    def enterDOMMode (self, attrs):
        """Actions upon first encountering an element for which we cannot create a binding.

        Invoking this transitions the parser into DOM mode, creating a new DOM
        document that will represent this element including its content."""
        assert not self.__domDocument
        self.__domDocument = pyxb.utils.saxdom.Document(namespace_context=self.namespaceContext())
        self.__domDepth = 0
        return self.startDOMElement(attrs)

    def startDOMElement (self, attrs):
        """Actions upon entering an element that is part of a DOM subtree."""
        self.__domDepth += 1
        self.__attributes = pyxb.utils.saxdom.NamedNodeMap()
        ns_ctx = self.namespaceContext()
        for name in attrs.getNames():
            attr_en = pyxb.namespace.ExpandedName(name)
            self.__attributes._addItem(pyxb.utils.saxdom.Attr(expanded_name=attr_en, namespace_context=ns_ctx, value=attrs.getValue(name), location=self.location()))

    def endDOMElement (self):
        """Actions upon leaving an element that is part of a DOM subtree."""
        ns_ctx = self.namespaceContext()
        element = pyxb.utils.saxdom.Element(namespace_context=ns_ctx, expanded_name=self.expandedName(), attributes=self.__attributes, location=self.location())
        for info in self.content():
            if isinstance(info.item, xml.dom.Node):
                element.appendChild(info.item)
            else:
                element.appendChild(pyxb.utils.saxdom.Text(info.item, namespace_context=ns_ctx))
        self.__domDepth -= 1
        if 0 == self.__domDepth:
            self.__domDocument.appendChild(element)
            #pyxb.utils.saxdom._DumpDOM(self.__domDocument)
            self.__domDepth = None
            self.__domDocument = None
        parent_state = self.parentState()
        parent_state.addElementContent(self.location(), element, None)
        return element

    def startBindingElement (self, type_class, new_object_factory, element_decl, attrs):
        """Actions upon entering an element that will produce a binding instance.

        The element use is recorded.  If the type is a subclass of
        L{basis.simpleTypeDefinition}, a delayed constructor is recorded so
        the binding instance can be created upon completion of the element;
        otherwise, a binding instance is created and stored.  The attributes
        are used to initialize the binding instance (now, or upon element
        end).

        @param type_class: The Python type of the binding instance
        @type type_class: subclass of L{basis._TypeBinding_mixin}
        @param new_object_factory: A callable object that creates an instance of the C{type_class}
        @param element_decl: The element use with which the binding instance is associated.  Will be C{None} for top-level elements
        @type element_decl: L{basis.element}
        @param attrs: The XML attributes associated with the element
        @type attrs: C{xml.sax.xmlreader.Attributes}
        @return: The generated binding instance, or C{None} if creation is delayed
        """
        self.__delayedConstructor = None
        self.__elementDecl = element_decl
        self.__attributes = attrs
        if type_class._IsSimpleTypeContent():
            self.__delayedConstructor = new_object_factory
        else:
            try:
                pyxb.namespace.NamespaceContext.PushContext(self.namespaceContext())
                self.__constructElement(new_object_factory, attrs)
            finally:
                pyxb.namespace.NamespaceContext.PopContext()
        return self.__bindingInstance

    def endBindingElement (self):
        """Perform any end-of-element processing.

        For simple type instances, this creates the binding instance.
        @return: The generated binding instance
        """
        if self.__delayedConstructor is not None:
            args = []
            for info in self.content():
                if info.maybe_element or (info.element_decl is not None):
                    raise pyxb.NonElementValidationError(info.item, info.location)
                args.append(info.item)
            try:
                pyxb.namespace.NamespaceContext.PushContext(self.namespaceContext())
                self.__constructElement(self.__delayedConstructor, self.__attributes, args)
            except pyxb.ValidationError as e:
                if e.location is None:
                    e.location = self.location()
                raise
            finally:
                pyxb.namespace.NamespaceContext.PopContext()
        else:
            for info in self.content():
                self.__bindingInstance.append(info.item,
                                              _element_decl=info.element_decl,
                                              _maybe_element=info.maybe_element,
                                              _location=info.location)
        parent_state = self.parentState()
        if parent_state is not None:
            parent_state.addElementContent(self.location(), self.__bindingInstance, self.__elementDecl)
        # As CreateFromDOM does, validate the resulting element
        if self.__bindingInstance._element() is None:
            self.__bindingInstance._setElement(self.__elementBinding)
        return self.__bindingInstance._postDOMValidate()

class PyXBSAXHandler (pyxb.utils.saxutils.BaseSAXHandler):
    """A SAX handler class which generates a binding instance for a document
    through a streaming parser.

    An example of using this to parse the document held in the (unicode) text
    value C{xmlt} is::

      import pyxb.binding.saxer
      import io

      saxer = pyxb.binding.saxer.make_parser()
      handler = saxer.getContentHandler()
      saxer.parse(io.StringIO(xmlt))
      instance = handler.rootObject()

    """

    # Whether invocation of handler methods should be traced
    __trace = False

    # An expanded name corresponding to xsi:type
    __XSITypeTuple = XSI.type.uriTuple()

    __domHandler = None
    __domDepth = None

    def rootObject (self):
        """Return the binding object corresponding to the top-most
        element in the document

        @return: An instance of L{basis._TypeBinding_mixin} (most usually a
        L{basis.complexTypeDefinition}.

        @raise pyxb.[UnrecognizedDOMRootNodeError: No binding could be found to
        match the top-level element in the document."""
        if not isinstance(self.__rootObject, basis._TypeBinding_mixin):
            # Happens if the top-level element got processed as a DOM instance.
            assert isinstance(self.__rootObject, xml.dom.Node)
            raise pyxb.UnrecognizedDOMRootNodeError(self.__rootObject)
        return self.__rootObject._postDOMValidate()
    __rootObject = None

    def reset (self):
        """Reset the state of the handler in preparation for processing a new
        document.

        @return: C{self}
        """
        super(PyXBSAXHandler, self).reset()
        self.__rootObject = None
        return self

    def __init__ (self, **kw):
        """Create a parser instance for converting XML to bindings.

        @keyword element_state_constructor: Overridden with the value
        L{_SAXElementState} before invoking the L{superclass
        constructor<pyxb.utils.saxutils.BaseSAXHandler.__init__>}.
        """

        kw.setdefault('element_state_constructor', _SAXElementState)
        super(PyXBSAXHandler, self).__init__(**kw)
        self.reset()

    def startElementNS (self, name, qname, attrs):
        (this_state, parent_state, ns_ctx, name_en) = super(PyXBSAXHandler, self).startElementNS(name, qname, attrs)

        # Delegate processing if in DOM mode
        if this_state.inDOMMode():
            return this_state.startDOMElement(attrs)

        # Resolve the element within the appropriate context.  Note
        # that global elements have no use, only the binding.
        if parent_state.enclosingCTD() is not None:
            (element_binding, element_decl) = parent_state.enclosingCTD()._ElementBindingDeclForName(name_en)
        else:
            element_decl = None
            element_binding = name_en.elementBinding()
        this_state.setElementBinding(element_binding)

        # Non-root elements should have an element use, from which we can
        # extract the binding if we couldn't find one elsewhere.  (Keep any
        # current binding, since it may be a member of a substitution group.)
        if (element_decl is not None) and (element_binding is None):
            assert self.__rootObject is not None
            element_binding = element_decl.elementBinding()
            assert element_binding is not None

        # Start knowing nothing
        type_class = None
        if element_binding is not None:
            element_binding = element_binding.elementForName(name)
            type_class = element_binding.typeDefinition()

        # Process an xsi:type attribute, if present
        if self.__XSITypeTuple in attrs:
            (did_replace, type_class) = XSI._InterpretTypeAttribute(attrs.getValue(self.__XSITypeTuple), ns_ctx, self.fallbackNamespace(), type_class)
            if did_replace:
                element_binding = None

        if type_class is None:
            # Bother.  We don't know what this thing is.  But that's not an
            # error, if the schema accepts wildcards.  For consistency with
            # the DOM-based interface, we need to build a DOM node.
            return this_state.enterDOMMode(attrs)

        if element_binding is not None:
            # Invoke binding __call__ method not Factory, so can check for
            # abstract elements.
            new_object_factory = element_binding
        else:
            new_object_factory = type_class.Factory

        # Update the enclosing complex type definition for this
        # element state.
        assert type_class is not None
        if issubclass(type_class, pyxb.binding.basis.complexTypeDefinition):
            this_state.setEnclosingCTD(type_class)
        else:
            this_state.setEnclosingCTD(parent_state.enclosingCTD())

        # Process the element start.  This may or may not return a
        # binding object.
        binding_object = this_state.startBindingElement(type_class, new_object_factory, element_decl, attrs)

        # If the top-level element has complex content, this sets the
        # root object.  If it has simple content, see endElementNS.
        if self.__rootObject is None:
            self.__rootObject = binding_object

    def endElementNS (self, name, qname):
        this_state = super(PyXBSAXHandler, self).endElementNS(name, qname)
        if this_state.inDOMMode():
            # Delegate processing if in DOM mode.  Note that completing this
            # element may take us out of DOM mode.  In any case, the returned
            # binding object is a DOM element instance.
            binding_object = this_state.endDOMElement()
        else:
            # Process the element end.  This will return a binding object,
            # either the one created at the start or the one created at
            # the end.
            binding_object = this_state.endBindingElement()
        assert binding_object is not None

        # If we don't have a root object, save it.  No, there is not a
        # problem doing this on the close of the element.  If the
        # top-level element has complex content, the object was
        # created on start, and the root object has been assigned.  If
        # it has simple content, then there are no internal elements
        # that could slip in and set this before we get to it here.
        #
        # Unless we're still in DOM mode, in which case this isn't really the
        # root object.  Then the real root object will be the one that caused
        # us to enter DOM mode.
        if (self.__rootObject is None) and not this_state.inDOMMode():
            self.__rootObject = binding_object

def make_parser (*args, **kw):
    """Extend L{pyxb.utils.saxutils.make_parser} to change the default
    C{content_handler_constructor} to be L{PyXBSAXHandler}.
    """
    kw.setdefault('content_handler_constructor', PyXBSAXHandler)
    return pyxb.utils.saxutils.make_parser(*args, **kw)

## Local Variables:
## fill-column:78
## End:
