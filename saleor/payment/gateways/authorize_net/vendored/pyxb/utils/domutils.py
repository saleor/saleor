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

"""Functions that support activities related to the Document Object Model."""

import logging
import xml.dom

import pyxb
import pyxb.namespace
import pyxb.namespace.resolution
import pyxb.utils.saxutils
import pyxb.utils.saxdom
from pyxb.utils import six
from pyxb.utils.six.moves import xrange

_log = logging.getLogger(__name__)

# The DOM implementation to be used for all processing.  Default is whatever
# your Python install uses, as long as it supports Core 2.0 (for
# createDocument) and XML 2.0 (for NS-aware attribute manipulation).  The
# built-in minidom works fine.
__DOMImplementation = xml.dom.getDOMImplementation(None, (('core', '2.0'), ('xml', '2.0')))

def GetDOMImplementation ():
    """Return the DOMImplementation object used for pyxb operations.

    This is primarily used as the default implementation when generating DOM
    trees from a binding instance.  It defaults to whatever
    xml.dom.getDOMImplementation() returns in your installation (often
    xml.dom.minidom).  It can be overridden with SetDOMImplementation()."""

    global __DOMImplementation
    return __DOMImplementation

def SetDOMImplementation (dom_implementation):
    """Override the default DOMImplementation object."""
    global __DOMImplementation
    __DOMImplementation = dom_implementation
    return __DOMImplementation

# Unfortunately, the DOMImplementation interface doesn't provide a parser.  So
# abstract this in case somebody wants to substitute a different one.  Haven't
# decided how to express that yet.
def StringToDOM (xml_text, **kw):
    """Convert string to a DOM instance.

    @see: L{pyxb._SetXMLStyle}."""

    xmlt = xml_text
    if pyxb.XMLStyle_minidom == pyxb._XMLStyle:
        parser = pyxb.utils.saxutils.make_parser()
        # minidom.parseString is broken.  In Python 2, this means don't
        # feed it unicode.  In Python 3 this means don't feed it bytes.
        if (six.PY2 and not isinstance(xmlt, six.binary_type)):
            xmlt = xmlt.encode(pyxb._InputEncoding)
        elif (six.PY3 and isinstance(xmlt, six.binary_type)):
            xmlt = xmlt.decode(pyxb._InputEncoding)
        return xml.dom.minidom.parseString(xmlt, parser)
    return pyxb.utils.saxdom.parseString(xml_text, **kw)

def NodeAttribute (node, attribute_ncname, attribute_ns=None):
    """Namespace-aware search for an optional attribute in a node.

    @param attribute_ncname: The local name of the attribute.
    @type attribute_ncname: C{str} or C{unicode}

    @keyword attribute_ns: The namespace of the attribute.  Defaults to None
    since most attributes are not in a namespace.  Can be provided as either a
    L{pyxb.namespace.Namespace} instance, or a string URI.
    @type attribute_ns: C{None} or C{str} or C{unicode} or L{pyxb.namespace.Namespace}

    @return: The value of the attribute, or C{None} if the attribute is not
    present.  (Unless C{None}, the value will always be a (unicode) string.)
    """

    ns_uri = attribute_ns
    if isinstance(attribute_ns, pyxb.namespace.Namespace):
        ns_uri = attribute_ns.uri()
    attr = node.getAttributeNodeNS(ns_uri, attribute_ncname)
    if attr is None:
        return None
    return attr.value

def NodeAttributeQName (node, attribute_ncname, attribute_ns=None):
    """Like L{NodeAttribute} but where the content is a QName that must be
    resolved in the context of the node.

    @param attribute_ncname: as in L{NodeAttribute}
    @keyword attribute_ns: as in L{NodeAttribute}

    @return: The expanded name to which the value of the attribute resolves
    given current namespaces, or C{None} if the attribute is not present
    @rtype: L{pyxb.namespace.ExpandedName}
    """
    attr = NodeAttribute(node, attribute_ncname, attribute_ns)
    if attr is None:
        return None
    nsc = pyxb.namespace.NamespaceContext.GetNodeContext(node)
    return nsc.interpretQName(attr)

def LocateUniqueChild (node, tag, absent_ok=True, namespace=pyxb.namespace.XMLSchema):
    """Locate a unique child of the DOM node.

    This function returns the sole child of node which is an ELEMENT_NODE
    instance and has a tag consistent with the given tag.  If multiple nodes
    with a matching C{tag} are found, or C{absent_ok} is C{False} and no
    matching tag is found, an exception is raised.

    @param node: An a xml.dom.Node ELEMENT_NODE instance
    @param tag: the NCName of an element in the namespace
    @keyword absent_ok: If C{True} (default), C{None} is returned if no match
    can be found.  If C{False}, an exception is raised if no match can be
    found.
    @keyword namespace: The namespace to which the child element belongs.
    Default is the XMLSchema namespace.
    @rtype: C{xml.dom.Node}

    @raise pyxb.SchemaValidationError: multiple elements are identified
    @raise pyxb.SchemaValidationError: C{absent_ok} is C{False} and no element is identified.
    """
    candidate = None
    for cn in node.childNodes:
        if (xml.dom.Node.ELEMENT_NODE == cn.nodeType) and namespace.nodeIsNamed(cn, tag):
            if candidate:
                raise pyxb.SchemaValidationError('Multiple %s elements nested in %s' % (tag, node.nodeName))
            candidate = cn
    if (candidate is None) and not absent_ok:
        raise pyxb.SchemaValidationError('Expected %s elements nested in %s' % (tag, node.nodeName))
    return candidate

def LocateMatchingChildren (node, tag, namespace=pyxb.namespace.XMLSchema):
    """Locate all children of the DOM node that have a particular tag.

    This function returns a list of children of node which are ELEMENT_NODE
    instances and have a tag consistent with the given tag.

    @param node: An a xml.dom.Node ELEMENT_NODE instance.
    @param tag: the NCName of an element in the namespace, which defaults to the
    XMLSchema namespace.
    @keyword namespace: The namespace to which the child element belongs.
    Default is the XMLSchema namespace.

    @rtype: C{list(xml.dom.Node)}
    """
    matches = []
    for cn in node.childNodes:
        if (xml.dom.Node.ELEMENT_NODE == cn.nodeType) and namespace.nodeIsNamed(cn, tag):
            matches.append(cn)
    return matches

def LocateFirstChildElement (node, absent_ok=True, require_unique=False, ignore_annotations=True):
    """Locate the first element child of the node.


    @param node: An a xml.dom.Node ELEMENT_NODE instance.
    @keyword absent_ok: If C{True} (default), C{None} is returned if no match
    can be found.  If C{False}, an exception is raised if no match can be
    found.
    @keyword require_unique: If C{False} (default), it is acceptable for there
    to be multiple child elements.  If C{True}, presence of multiple child
    elements raises an exception.
    @keyword ignore_annotations: If C{True} (default), annotations are skipped
    wheen looking for the first child element.  If C{False}, an annotation
    counts as an element.
    @rtype: C{xml.dom.Node}

    @raise SchemaValidationError: C{absent_ok} is C{False} and no child
    element was identified.
    @raise SchemaValidationError: C{require_unique} is C{True} and multiple
    child elements were identified
    """

    candidate = None
    for cn in node.childNodes:
        if xml.dom.Node.ELEMENT_NODE == cn.nodeType:
            if ignore_annotations and pyxb.namespace.XMLSchema.nodeIsNamed(cn, 'annotation'):
                continue
            if require_unique:
                if candidate:
                    raise pyxb.SchemaValidationError('Multiple elements nested in %s' % (node.nodeName,))
                candidate = cn
            else:
                return cn
    if (candidate is None) and not absent_ok:
        raise pyxb.SchemaValidationError('No elements nested in %s' % (node.nodeName,))
    return candidate

def HasNonAnnotationChild (node):
    """Return True iff C{node} has an ELEMENT_NODE child that is not an
    XMLSchema annotation node.

    @rtype: C{bool}
    """
    for cn in node.childNodes:
        if (xml.dom.Node.ELEMENT_NODE == cn.nodeType) and (not pyxb.namespace.XMLSchema.nodeIsNamed(cn, 'annotation')):
            return True
    return False

def ExtractTextContent (node):
    """Walk all the children, extracting all text content and
    catenating it into the return value.

    Returns C{None} if no text content (including whitespace) is found.

    This is mainly used to strip comments out of the content of complex
    elements with simple types.

    @rtype: C{unicode} or C{str}
    """
    text = []
    for cn in node.childNodes:
        if xml.dom.Node.TEXT_NODE == cn.nodeType:
            text.append(cn.data)
        elif xml.dom.Node.CDATA_SECTION_NODE == cn.nodeType:
            text.append(cn.data)
        elif xml.dom.Node.COMMENT_NODE == cn.nodeType:
            pass
        else:
            raise pyxb.NonElementValidationError(cn)
    if 0 == len(text):
        return None
    return ''.join(text)

class BindingDOMSupport (object):
    """This holds DOM-related information used when generating a DOM tree from
    a binding instance."""

    def implementation (self):
        """The DOMImplementation object to be used.

        Defaults to L{pyxb.utils.domutils.GetDOMImplementation()}, but can be
        overridden in the constructor call using the C{implementation}
        keyword."""
        return self.__implementation
    __implementation = None

    def document (self):
        """Return the document generated using this instance."""
        return self.__document
    __document = None

    def requireXSIType (self):
        """Indicates whether {xsi:type<http://www.w3.org/TR/xmlschema-1/#xsi_type>} should be added to all elements.

        Certain WSDL styles and encodings seem to require explicit notation of
        the type of each element, even if it was specified in the schema.

        This value can only be set in the constructor."""
        return self.__requireXSIType
    __requireXSIType = None

    def reset (self):
        """Reset this instance to the state it was when created.

        This creates a new root document with no content, resets the
        namespace-prefix map to its as-constructed content, and clears the set
        of referenced namespace prefixes.  The defaultNamespace and
        requireXSIType are not modified."""
        self.__document = self.implementation().createDocument(None, None, None)
        self.__namespaceContext.reset()
        # For historical reasons this is also added automatically, though
        # 'xsi' is not a bound prefix.
        self.__namespaceContext.declareNamespace(pyxb.namespace.XMLSchema_instance, 'xsi')
        self.__referencedNamespacePrefixes = set()

    @classmethod
    def Reset (cls):
        """Reset the global defaults for default/prefix/namespace information."""
        cls.__NamespaceContext.reset()

    def __init__ (self, implementation=None, default_namespace=None, require_xsi_type=False, namespace_prefix_map=None):
        """Create a new instance used for building a single document.

        @keyword implementation: The C{xml.dom} implementation to use.
        Defaults to the one selected by L{GetDOMImplementation}.

        @keyword default_namespace: The namespace to configure as the default
        for the document.  If not provided, there is no default namespace.
        @type default_namespace: L{pyxb.namespace.Namespace}

        @keyword require_xsi_type: If C{True}, an U{xsi:type
        <http://www.w3.org/TR/xmlschema-1/#xsi_type>} attribute should be
        placed in every element.
        @type require_xsi_type: C{bool}

        @keyword namespace_prefix_map: A map from pyxb.namespace.Namespace
        instances to the preferred prefix to use for the namespace in xmlns
        declarations.  The default one assigns 'xsi' for the XMLSchema
        instance namespace.
        @type namespace_prefix_map: C{map} from L{pyxb.namespace.Namespace} to C{str}

        @raise pyxb.LogicError: the same prefix is associated with multiple
        namespaces in the C{namespace_prefix_map}.

        """
        if implementation is None:
            implementation = GetDOMImplementation()
        self.__implementation = implementation
        self.__requireXSIType = require_xsi_type
        self.__namespaceContext = pyxb.namespace.NamespaceContext(parent_context=self.__NamespaceContext,
                                                                  in_scope_namespaces=namespace_prefix_map)
        if default_namespace is not None:
            self.__namespaceContext.setDefaultNamespace(default_namespace)
        self.reset()

    # Default namespace-prefix map support
    __NamespaceContext = pyxb.namespace.NamespaceContext()

    # Instance-specific namespace-prefix map support
    __namespaceContext = None

    # Set of pairs of (namespace, prefix) identifying the declarations that
    # must be placed in the document root so that QNames can be resolved.
    # These are the prefixes associated with namespaces that were queried
    # through L{namespacePrefix()} since the last reset().
    __referencedNamespacePrefixes = None

    def defaultNamespace (self):
        """The default namespace for this instance"""
        return self.__namespaceContext.defaultNamespace()
    @classmethod
    def DefaultNamespace (cls):
        """The global default namespace (used on instance creation if not overridden)"""
        return cls.__NamespaceContext.defaultNamespace()

    def setDefaultNamespace (self, default_namespace):
        return self.__namespaceContext.setDefaultNamespace(default_namespace)
    @classmethod
    def SetDefaultNamespace (cls, default_namespace):
        return cls.__NamespaceContext.setDefaultNamespace(default_namespace)

    def declareNamespace (self, namespace, prefix=None):
        """Declare a namespace within this instance only."""
        return self.__namespaceContext.declareNamespace(namespace, prefix)
    @classmethod
    def DeclareNamespace (cls, namespace, prefix=None):
        """Declare a namespace that will made available to each created instance."""
        return cls.__NamespaceContext.declareNamespace(namespace, prefix)

    def namespacePrefix (self, namespace, enable_default_namespace=True):
        """Return the prefix to be used for the given namespace.

        This will L{declare <declareNamespace>} the namespace if it has not
        yet been observed.  It will also ensure the mapping from the returned
        prefix to C{namespace} is recorded for addition as an xmlns directive
        in the final document.

        @param namespace: The namespace for which a prefix is needed.  If the
        provided namespace is C{None} or an absent namespace, the C{None}
        value will be returned as the corresponding prefix.

        @keyword enable_default_namespace: Normally if the namespace is the default
        namespace C{None} is returned to indicate this.  If this keyword is
        C{False} then we need a namespace prefix even if this is the default.
        """
        if (namespace is None) or namespace.isAbsentNamespace():
            return None
        if isinstance(namespace, six.string_types):
            namespace = pyxb.namespace.NamespaceForURI(namespace, create_if_missing=True)
        if (self.defaultNamespace() == namespace) and enable_default_namespace:
            return None
        pfx = self.__namespaceContext.prefixForNamespace(namespace)
        if pfx is None:
            pfx = self.__namespaceContext.declareNamespace(namespace)
        self.__referencedNamespacePrefixes.add((namespace, pfx))
        return pfx

    def qnameAsText (self, qname, enable_default_namespace=True):
        assert isinstance(qname, pyxb.namespace.ExpandedName)
        name = qname.localName()
        prefix = self.namespacePrefix(qname.namespace(), enable_default_namespace=enable_default_namespace)
        if prefix is not None:
            name = '%s:%s' % (prefix, name)
        return name

    def valueAsText (self, value, enable_default_namespace=True):
        """Represent a simple type value as XML text.

        This is essentially what C{value.xsdLiteral()} does, but this one
        handles any special cases such as QName values where the lexical
        representation cannot be done in isolation of external information
        such as namespace declarations."""
        from pyxb.binding.basis import simpleTypeDefinition, STD_list
        if isinstance(value, pyxb.namespace.ExpandedName):
            return self.qnameAsText(value, enable_default_namespace=enable_default_namespace)
        if isinstance(value, STD_list):
            return ' '.join([ self.valueAsText(_v, enable_default_namespace=enable_default_namespace) for _v in value ])
        if isinstance(value, simpleTypeDefinition):
            return value.xsdLiteral()
        assert value is not None
        return six.text_type(value)

    def addAttribute (self, element, expanded_name, value):
        """Add an attribute to the given element.

        @param element: The element to which the attribute should be added
        @type element: C{xml.dom.Element}
        @param expanded_name: The name of the attribute.  This may be a local
        name if the attribute is not in a namespace.
        @type expanded_name: L{pyxb.namespace.Namespace} or C{str} or C{unicode}
        @param value: The value of the attribute
        @type value: C{str} or C{unicode}
        """
        name = expanded_name
        ns_uri = xml.dom.EMPTY_NAMESPACE
        if isinstance(name, pyxb.namespace.ExpandedName):
            ns_uri = expanded_name.namespaceURI()
            # Attribute names do not use default namespace
            name = self.qnameAsText(expanded_name, enable_default_namespace=False)
        element.setAttributeNS(ns_uri, name, self.valueAsText(value))

    def addXMLNSDeclaration (self, element, namespace, prefix=None):
        """Manually add an XMLNS declaration to the document element.

        @param namespace: a L{pyxb.namespace.Namespace} instance

        @param prefix: the prefix by which the namespace is known.  If
        C{None}, the default prefix as previously declared will be used; if
        C{''} (empty string) a declaration for C{namespace} as the default
        namespace will be generated.

        @return: C{prefix} as used in the added declaration.
        """
        if not isinstance(namespace, pyxb.namespace.Namespace):
            raise pyxb.UsageError('addXMLNSdeclaration: must be given a namespace instance')
        if namespace.isAbsentNamespace():
            raise pyxb.UsageError('addXMLNSdeclaration: namespace must not be an absent namespace')
        if prefix is None:
            prefix = self.namespacePrefix(namespace)
        if not prefix: # None or empty string
            an = 'xmlns'
        else:
            an = 'xmlns:' + prefix
        element.setAttributeNS(pyxb.namespace.XMLNamespaces.uri(), an, namespace.uri())
        return prefix

    def finalize (self):
        """Do the final cleanup after generating the tree.  This makes sure
        that the document element includes XML Namespace declarations for all
        namespaces referenced in the tree.

        @return: The document that has been created.
        @rtype: C{xml.dom.Document}"""
        ns = self.defaultNamespace()
        if ns is not None:
            self.addXMLNSDeclaration(self.document().documentElement, ns, '')
        for (ns, pfx) in self.__referencedNamespacePrefixes:
            self.addXMLNSDeclaration(self.document().documentElement, ns, pfx)
        return self.document()

    def createChildElement (self, expanded_name, parent=None):
        """Create a new element node in the tree.

        @param expanded_name: The name of the element.  A plain string
        indicates a name in no namespace.
        @type expanded_name: L{pyxb.namespace.ExpandedName} or C{str} or C{unicode}

        @keyword parent: The node in the tree that will serve as the child's
        parent.  If C{None}, the document element is used.  (If there is no
        document element, then this call creates it as a side-effect.)

        @return: A newly created DOM element
        @rtype: C{xml.dom.Element}
        """

        if parent is None:
            parent = self.document().documentElement
        if parent is None:
            parent = self.__document
        if isinstance(expanded_name, six.string_types):
            expanded_name = pyxb.namespace.ExpandedName(None, expanded_name)
        if not isinstance(expanded_name, pyxb.namespace.ExpandedName):
            raise pyxb.LogicError('Invalid type %s for expanded name' % (type(expanded_name),))
        ns = expanded_name.namespace()
        ns_uri = xml.dom.EMPTY_NAMESPACE
        name = expanded_name.localName()
        if ns is not None:
            ns_uri = ns.uri()
            name = self.qnameAsText(expanded_name)
        element = self.__document.createElementNS(ns_uri, name)
        return parent.appendChild(element)

    def _makeURINodeNamePair (self, node):
        """Convert namespace information from a DOM node to text for new DOM node.

        The namespaceURI and nodeName are extracted and parsed.  The namespace
        (if any) is registered within the document, along with any prefix from
        the node name.  A pair is returned where the first element is the
        namespace URI or C{None}, and the second is a QName to be used for the
        expanded name within this document.

        @param node: An xml.dom.Node instance, presumably from a wildcard match.
        @rtype: C{( str, str )}"""
        ns = None
        if node.namespaceURI is not None:
            ns = pyxb.namespace.NamespaceForURI(node.namespaceURI, create_if_missing=True)
        if node.ELEMENT_NODE == node.nodeType:
            name = node.tagName
        elif node.ATTRIBUTE_NODE == node.nodeType:
            name = node.name
            # saxdom uses the uriTuple as the name field while minidom uses
            # the QName.  @todo saxdom should be fixed.
            if isinstance(name, tuple):
                name = name[1]
        else:
            raise pyxb.UsageError('Unable to determine name from DOM node %s' % (node,))
        pfx = None
        local_name = name
        if 0 < name.find(':'):
            (pfx, local_name) = name.split(':', 1)
            if ns is None:
                raise pyxb.LogicError('QName with prefix but no available namespace')
        ns_uri = None
        node_name = local_name
        if ns is not None:
            ns_uri = ns.uri()
            self.declareNamespace(ns, pfx)
            node_name = self.qnameAsText(ns.createExpandedName(local_name))
        return (ns_uri, node_name)

    def _deepClone (self, node, docnode):
        if node.ELEMENT_NODE == node.nodeType:
            (ns_uri, node_name) = self._makeURINodeNamePair(node)
            clone_node = docnode.createElementNS(ns_uri, node_name)
            attrs = node.attributes
            for ai in xrange(attrs.length):
                clone_node.setAttributeNodeNS(self._deepClone(attrs.item(ai), docnode))
            for child in node.childNodes:
                clone_node.appendChild(self._deepClone(child, docnode))
            return clone_node
        if node.TEXT_NODE == node.nodeType:
            return docnode.createTextNode(node.data)
        if node.ATTRIBUTE_NODE == node.nodeType:
            (ns_uri, node_name) = self._makeURINodeNamePair(node)
            clone_node = docnode.createAttributeNS(ns_uri, node_name)
            clone_node.value = node.value
            return clone_node
        if node.COMMENT_NODE == node.nodeType:
            return docnode.createComment(node.data)
        raise ValueError('DOM node not supported in clone', node)

    def cloneIntoImplementation (self, node):
        """Create a deep copy of the node in the target implementation.

        Used when converting a DOM instance from one implementation (e.g.,
        L{pyxb.utils.saxdom}) into another (e.g., L{xml.dom.minidom})."""
        new_doc = self.implementation().createDocument(None, None, None)
        return self._deepClone(node, new_doc)

    def appendChild (self, child, parent):
        """Add the child to the parent.

        @note: If the child and the parent use different DOM implementations,
        this operation will clone the child into a new instance, and give that
        to the parent.

        @param child: The value to be appended
        @type child: C{xml.dom.Node}
        @param parent: The new parent of the child
        @type parent: C{xml.dom.Node}
        @rtype: C{xml.dom.Node}"""

        # @todo This check is incomplete; is there a standard way to find the
        # implementation of an xml.dom.Node instance?
        if isinstance(child, (pyxb.utils.saxdom.Node, xml.dom.minidom.Node)):
            child = self.cloneIntoImplementation(child)
        return parent.appendChild(child)

    def appendTextChild (self, text, parent):
        """Add the text to the parent as a text node."""
        return parent.appendChild(self.document().createTextNode(self.valueAsText(text)))

## Local Variables:
## fill-column:78
## End:
