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

from __future__ import print_function
from pyxb.bundles.wssplat.raw.wsdl11 import *
import pyxb.bundles.wssplat.raw.wsdl11 as raw_wsdl11

import pyxb.namespace
from pyxb.utils import domutils, six
import xml.dom

def ImportRelatedNamespaces ():
    """Import modules for related namespaces so they are available to
    create binding instances from the WSDL sources."""
    try:
        import pyxb.bundles.wssplat.soapbind11
    except ImportError:
        pass
    try:
        import pyxb.bundles.wssplat.soapbind12
    except ImportError:
        pass
    try:
        import pyxb.bundles.wssplat.soap11
    except ImportError:
        pass
    try:
        import pyxb.bundles.wssplat.soap12
    except ImportError:
        pass
    try:
        import pyxb.bundles.wssplat.soapenv
    except ImportError:
        pass
    try:
        import pyxb.bundles.wssplat.httpbind
    except ImportError:
        pass
    try:
        import pyxb.bundles.wssplat.mimebind
    except ImportError:
        pass


class _WSDL_binding_mixin (object):
    """Mix-in class to mark element Python bindings that are expected
    to be wildcard matches in WSDL binding elements."""
    pass

class _WSDL_port_mixin (object):
    """Mix-in class to mark element Python bindings that are expected
    to be wildcard matches in WSDL port elements."""
    pass

class _WSDL_operation_mixin (object):
    """Mix-in class to mark element Python bindings that are expected
    to be wildcard matches in WSDL (binding) operation elements."""
    pass

class tPort (raw_wsdl11.tPort):
    def __getBindingReference (self):
        return self.__bindingReference
    def _setBindingReference (self, binding_reference):
        self.__bindingReference = binding_reference
    __bindingReference = None
    bindingReference = property(__getBindingReference)

    def __getAddressReference (self):
        return self.__addressReference
    def _setAddressReference (self, address_reference):
        self.__addressReference = address_reference
    __addressReference = None
    addressReference = property(__getAddressReference)

raw_wsdl11.tPort._SetSupersedingClass(tPort)

class tBinding (raw_wsdl11.tBinding):
    def __getPortTypeReference (self):
        return self.__portTypeReference
    def setPortTypeReference (self, port_type_reference):
        self.__portTypeReference = port_type_reference
    __portTypeReference = None
    portTypeReference = property(__getPortTypeReference)

    def __getProtocolBinding (self):
        """Return the protocol-specific binding information."""
        return self.__protocolBinding
    def _setProtocolBinding (self, protocol_binding):
        self.__protocolBinding = protocol_binding
    __protocolBinding = None
    protocolBinding = property(__getProtocolBinding)

    def operationMap (self):
        return self.__operationMap
    __operationMap = None

    def __init__ (self, *args, **kw):
        super(tBinding, self).__init__(*args, **kw)
        self.__operationMap = { }
raw_wsdl11.tBinding._SetSupersedingClass(tBinding)

class tPortType (raw_wsdl11.tPortType):
    def operationMap (self):
        return self.__operationMap
    __operationMap = None

    def __init__ (self, *args, **kw):
        super(tPortType, self).__init__(*args, **kw)
        self.__operationMap = { }
raw_wsdl11.tPortType._SetSupersedingClass(tPortType)

class tParam (raw_wsdl11.tParam):
    def __getMessageReference (self):
        return self.__messageReference
    def _setMessageReference (self, message_reference):
        self.__messageReference = message_reference
    __messageReference = None
    messageReference = property(__getMessageReference)
raw_wsdl11.tParam._SetSupersedingClass(tParam)

class tFault (raw_wsdl11.tFault):
    def __getMessageReference (self):
        return self.__messageReference
    def _setMessageReference (self, message_reference):
        self.__messageReference = message_reference
    __messageReference = None
    messageReference = property(__getMessageReference)
raw_wsdl11.tFault._SetSupersedingClass(tFault)

class tPart (raw_wsdl11.tPart):
    def __getElementReference (self):
        return self.__elementReference
    def _setElementReference (self, element_reference):
        self.__elementReference = element_reference
    __elementReference = None
    elementReference = property(__getElementReference)

    def __getTypeReference (self):
        return self.__typeReference
    def _setTypeReference (self, type_reference):
        self.__typeReference = type_reference
    __typeReference = None
    typeReference = property(__getTypeReference)
raw_wsdl11.tPart._SetSupersedingClass(tPart)

class tBindingOperation (raw_wsdl11.tBindingOperation):
    def __getOperationReference (self):
        return self.__operationReference
    def _setOperationReference (self, operation_reference):
        self.__operationReference = operation_reference
    __operationReference = None
    operationReference = property(__getOperationReference)
raw_wsdl11.tBindingOperation._SetSupersedingClass(tBindingOperation)

class tDefinitions (raw_wsdl11.tDefinitions):
    def messageMap (self):
        return self.targetNamespace().messages()

    def namespaceContext (self):
        return self.__namespaceContext
    __namespaceContext = None

    def bindingMap (self):
        return self.__bindingMap
    __bindingMap = None

    def targetNamespace (self):
        return self.namespaceContext().targetNamespace()

    def namespace (self):
        return self.__namespace
    __namespace = None

    def _addToMap (self, map, qname, value):
        map[qname] = value
        (ns, ln) = qname
        if (ns == self.targetNamespace()):
            map[(None, ln)] = value
        elif (ns is None):
            map[(self.targetNamespace(), ln)] = value
        return map

    def schema (self):
        return self.__schema
    __schema = None

    @classmethod
    def _PreFactory_vx (self, args, kw):
        # Import standard bindings.  If we do this, then wildcard
        # binding, port, and operation elements will be recognized and
        # converted into bindings.
        import pyxb.bundles.wssplat.soapbind11
        import pyxb.bundles.wssplat.soapbind12
        import pyxb.bundles.wssplat.httpbind

        # Ensure we have definitions for any externally-referenced
        # things we might need.  @todo: This might have to
        # chronologically precede the import above.
        pyxb.namespace.archive.NamespaceArchive.PreLoadArchives()

        raw_wsdl11.Namespace.validateComponentModel()
        state = ( kw.pop('process_schema', False),
                  kw.pop('generation_uid', None),
                  kw.get('_dom_node') )
        return state

    def _postFactory_vx (self, state):
        (process_schema, generation_uid, dom_node) = state
        assert isinstance(dom_node, xml.dom.Node)
        node_en = pyxb.namespace.ExpandedName(dom_node)
        self.__namespaceContext = pyxb.namespace.NamespaceContext.GetNodeContext(dom_node)
        self.__buildMaps()
        if process_schema:
            self.__processSchema(generation_uid)
        self.__finalizeReferences()
        return self

    __WSDLCategories = ( 'service', 'port', 'message', 'binding', 'portType' )
    def __buildMaps (self):
        tns = self.namespaceContext().targetNamespace()
        tns.configureCategories(self.__WSDLCategories)
        for m in self.message:
            tns.messages()[m.name] = m
        for pt in self.portType:
            tns.portTypes()[pt.name] = pt
            for op in pt.operation:
                pt.operationMap()[op.name] = op
                params = op.fault[:]
                if op.input is not None:
                    params.append(op.input)
                if op.output is not None:
                    params.append(op.output)
                for p in params:
                    msg_en = p.message
                    p._setMessageReference(p.message.message())
        for b in self.binding:
            tns.bindings()[b.name] = b
            port_type_en = b.type
            b.setPortTypeReference(port_type_en.portType())
            for wc in b.wildcardElements():
                if isinstance(wc, _WSDL_binding_mixin):
                    b._setProtocolBinding(wc)
                    break
            for op in b.operation:
                b.operationMap()[op.name] = op
                for wc in op.wildcardElements():
                    if isinstance(wc, _WSDL_operation_mixin):
                        op._setOperationReference(wc)
                        break
        for s in self.service:
            tns.services()[s.name] = s
            for p in s.port:
                binding_en = p.binding
                p._setBindingReference(binding_en.binding())
                for wc in p.wildcardElements():
                    if isinstance(wc, _WSDL_port_mixin):
                        p._setAddressReference(wc)
                        break

    def __processSchema (self, generation_uid):
        global pyxb
        import pyxb.xmlschema

        print('PS %s' % (generation_uid,))
        if self.__schema is not None:
            print('Already have schema')
            return self.__schema
        for t in self.types:
            for wc in t.wildcardElements():
                if isinstance(wc, xml.dom.Node) and pyxb.namespace.XMLSchema.nodeIsNamed(wc, 'schema'):
                    # Try to load component models for any namespace referenced by this.
                    # Probably shouldn't need to do this except for imported ones.
                    for ns in six.itervalues(self.namespaceContext().inScopeNamespaces()):
                        try:
                            ns.validateComponentModel()
                        except Exception as e:
                            print('Error validating component model for %s: %s' % (ns.uri(), e))
                    self.__schema = pyxb.xmlschema.schema.CreateFromDOM(wc, namespace_context=self.namespaceContext(), generation_uid=generation_uid)
                elif isinstance(wc, pyxb.xmlschema.schema):
                    self.__schema = wc
                else:
                    print('No match: %s %s' % (wc.namespaceURI, namespace.localName))
                if self.__schema is not None:
                    return self.__schema
        return None

    def __finalizeReferences (self):
        tns = self.namespaceContext().targetNamespace()
        for m in six.itervalues(tns.messages()):
            for p in m.part:
                if (p.element is not None) and (p.elementReference is None):
                    elt_en = p.element
                    p._setElementReference(elt_en.elementDeclaration())
                if (p.type is not None) and (p.typeReference is None):
                    type_en = p.type
                    p._setTypeReference(type_en.typeDefinition())

raw_wsdl11.tDefinitions._SetSupersedingClass(tDefinitions)

pyxb.namespace.NamespaceContext._AddTargetNamespaceAttribute(raw_wsdl11.Namespace.createExpandedName('definitions'), pyxb.namespace.ExpandedName('targetNamespace'))
