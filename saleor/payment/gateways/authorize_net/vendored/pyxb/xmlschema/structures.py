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

"""Classes corresponding to W3C XML Schema components.

Class names and behavior should conform to the schema components described in
U{XML Schema Part 1: Structures<http://www.w3.org/TR/xmlschema-1/>}.
References to sections in the documentation of this module generally refers to
that document.

Each class has a C{CreateFromDOM} class method that creates an instance and
initializes it from a DOM node.  Only the L{Wildcard}, L{Particle}, and
L{ModelGroup} components are created from non-DOM sources.  However, the
requirements on DOM interface are restricted to attributes, child nodes, and
basic fields, though all these must support namespaces.

@group Mixins: *_mixin
@group Ur Type Specializations: *UrType*
@group Utilities: _ImportElementInformationItem

"""

import re
import logging
from xml.dom import Node
import copy
from pyxb.utils.six.moves.urllib import parse as urlparse
import os.path

import pyxb
import pyxb.xmlschema
import pyxb.namespace.archive
import pyxb.namespace.resolution

from pyxb.binding import basis, datatypes, facets
from pyxb.utils import domutils, six
import pyxb.utils.utility

_log = logging.getLogger(__name__)

# Flag indicating that the built in types have been registered
_PastAddBuiltInTypes = False

# Make it easier to check node names in the XMLSchema namespace
from pyxb.namespace import XMLSchema as xsd

class _SchemaComponent_mixin (pyxb.namespace._ComponentDependency_mixin,
                              pyxb.namespace.archive._ArchivableObject_mixin,
                              pyxb.utils.utility.PrivateTransient_mixin,
                              pyxb.utils.utility.Locatable_mixin):
    """A mix-in that marks the class as representing a schema component.

    This exists so that we can determine the owning schema for any
    component we encounter.  This is normally done at construction
    time by passing a C{schema=val} parameter to the constructor.
    """

    # This class suppports transient instance variables.  These variables are
    # added to the set of transients at the point of declaration in the class.
    __PrivateTransient = set()

    def _namespaceContext (self):
        """The namespace context for this schema.

        This defines where it looks things up, where it puts things it
        creates, the in-scope namespace declarations, etc.  Must be defined
        for anything that does any sort of QName interpretation.  The value is
        generally a reference to a namespace context associated with the DOM
        element node corresponding to this component."""
        if self.__namespaceContext is None:
            raise pyxb.LogicError('Attempt to access missing namespace context for %s' % (self,))
        return self.__namespaceContext
    def _clearNamespaceContext (self):
        # Calculate the binding sort key for any archive before we discard the
        # namespace context, which we might need.
        self.schemaOrderSortKey()
        self.__namespaceContext = None
        return self
    __namespaceContext = None
    __PrivateTransient.add('namespaceContext')

    # The name by which this component is known within the binding module.
    # This is in component rather than _NamedComponent_mixin because some
    # unnamed components (like ModelGroup and Wildcard) have Python objects to
    # represent them, so need a binding-level name.
    __nameInBinding = None

    # The schema component that owns this.  If C{None}, the component is owned
    # directly by the schema.
    __owner = None
    __PrivateTransient.add('owner')

    # The schema components owned by this component.
    __ownedComponents = None
    __PrivateTransient.add('ownedComponent')

    def _scope (self):
        """The context into which declarations in or subordinate to this node are placed."""
        return self.__scope
    __scope = None

    def _scopeIsIndeterminate (self):
        """Return True iff nobody has defined a scope for this node."""
        return _ScopedDeclaration_mixin.ScopeIsIndeterminate(self._scope())

    def _scopeIsGlobal (self):
        """Return True iff this component has global scope."""
        return _ScopedDeclaration_mixin.ScopeIsGlobal(self._scope())

    def _setScope (self, ctd):
        """Set the scope of this instance after construction.

        This should only be invoked on cloned declarations being incorporated
        into a complex type definition.  Note that the source of the clone may
        be any scope: indeterminate if from a model (attribute) group
        definition; global if a reference to a global component; or ctd if
        inherited from a complex base type."""
        assert self.__cloneSource is not None
        assert isinstance(self, _ScopedDeclaration_mixin)
        assert isinstance(ctd, ComplexTypeDefinition)
        self.__scope = ctd
        return self

    def __init__ (self, *args, **kw):
        """Initialize portions of a component.

        @keyword scope: The scope in which the component is defined

        @keyword namespace_context: The NamespaceContext to use within this component

        @keyword node: If no C{namespace_context} is provided, a DOM node must
        be provided from which a namespace context can be identified.

        @keyword owner: Reference to the component that owns this one (the
        immediately enclosing component).  Is C{None} in the case of top-level
        components.

        @keyword schema: Reference to the L{Schema} component to which the
        component belongs.  Required for every component except L{Schema},
        L{Annotation}, and L{Wildcard}.
        """

        self.__ownedComponents = set()
        self.__scope = kw.get('scope')
        self.__namespaceContext = kw.get('namespace_context')
        node = kw.get('node')
        owner = kw.get('owner')
        if self.__namespaceContext is None:
            if node is None:
                raise pyxb.LogicError('Schema component constructor must be given namespace_context or node')
            self.__namespaceContext = pyxb.namespace.NamespaceContext.GetNodeContext(node)
        if self.__namespaceContext is None:
            raise pyxb.LogicError('No namespace_context for schema component')

        super(_SchemaComponent_mixin, self).__init__(*args, **kw)

        self._namespaceContext().targetNamespace()._associateComponent(self)

        self._setOwner(owner)
        if isinstance(node, pyxb.utils.utility.Locatable_mixin):
            self._setLocation(node._location())
        elif isinstance(owner, pyxb.utils.utility.Locatable_mixin):
            self._setLocation(owner._location())

        schema = kw.get('schema')
        if schema is not None:
            self._setObjectOrigin(schema.originRecord())
        else:
            assert isinstance(self, (Schema, Annotation, Wildcard)), 'No origin available for type %s' % (type(self),)

        if isinstance(self, ComplexTypeDefinition):
            assert 1 < len(self.__namespaceContext.inScopeNamespaces())

    def _dissociateFromNamespace (self):
        """Dissociate this component from its owning namespace.

        This should only be done whwen there are no other references to the
        component, and you want to ensure it does not appear in the model."""
        self._namespaceContext().targetNamespace()._replaceComponent(self, None)
        return self

    def _setOwner (self, owner):
        """Set the owner of this component.

        If C{owner} is C{None}, this has no effect.  Otherwise, the
        component's current owner must be either C{None} or the same as the
        input C{owner}."""

        if owner is not None:
            assert (self.__owner is None) or (self.__owner == owner), 'Owner was %s set to %s' % (self.__owner, owner)
            self.__owner = owner
            owner.__ownedComponents.add(self)
        return self

    def owner (self):
        return self.__owner

    # A reference to the instance from which this instance was cloned.
    __cloneSource = None
    __PrivateTransient.add('cloneSource')

    def _cloneSource (self):
        """The source component from which this is a clone.

        Returns C{None} if this is not a clone."""
        return self.__cloneSource

    # A set of references to all instances that are clones of this one.
    __clones = None
    __PrivateTransient.add('clones')

    def _clones (self):
        """The set of instances cloned from this component.

        Returns None if no instances have been cloned from this."""
        return self.__clones

    def _resetClone_csc (self, **kw):
        """Virtual method to clear whatever attributes should be reset in a
        cloned component.

        This instance should be an instance created by copy.copy().

        The implementation in this class clears the owner and dependency
        relations.

        Returns C{self}.
        """
        assert self.__cloneSource is not None
        owner = kw['owner']
        self.__nameInBinding = None
        self.__owner = owner
        assert not (isinstance(self, ComplexTypeDefinition) and isinstance(owner, Schema))
        self.__ownedComponents = set()
        self.__clones = None
        owner._namespaceContext().targetNamespace()._associateComponent(self)
        if self.__namespaceContext is None:
            # When cloning imported components, loan them the owner's
            # namespace context, only so that their cloned children can be
            # associated with the same namespace.
            self.__namespaceContext = owner._namespaceContext()
        self_fn = lambda *_args, **_kw: self
        return getattr(super(_SchemaComponent_mixin, self), '_resetClone_csc', self_fn)(**kw)

    def _clone (self, owner, origin):
        """Create a copy of this instance suitable for adoption by some other
        component.

        This is used for creating a locally-scoped declaration from a
        declaration in a named model or attribute group."""

        # We only care about cloning declarations, and they should
        # have an unassigned scope.  However, we do clone
        # non-declarations that contain cloned declarations.
        #assert (not isinstance(self, _ScopedDeclaration_mixin)) or self._scopeIsIndeterminate()
        if isinstance(self, pyxb.namespace.resolution._Resolvable_mixin):
            assert self.isResolved()

        assert owner is not None
        that = copy.copy(self)
        that.__cloneSource = self
        if self.__clones is None:
            self.__clones = set()
        self.__clones.add(that)
        that._resetClone_csc(owner=owner, origin=origin)
        if isinstance(that, pyxb.namespace.resolution._Resolvable_mixin):
            assert that.isResolved()
        return that

    def isTypeDefinition (self):
        """Return True iff this component is a simple or complex type
        definition."""
        return isinstance(self, (SimpleTypeDefinition, ComplexTypeDefinition))

    def isUrTypeDefinition (self):
        """Return True iff this component is a simple or complex type
        definition."""
        return isinstance(self, (_SimpleUrTypeDefinition, _UrTypeDefinition))

    def bestNCName (self):
        """Return the name of this component, as best it can be determined.

        For example, ModelGroup instances will be named by their
        ModelGroupDefinition, if available.  Returns None if no name can be
        inferred."""
        if isinstance(self, _NamedComponent_mixin):
            return self.name()
        if isinstance(self, ModelGroup):
            agd = self.modelGroupDefinition()
            if agd is not None:
                return agd.name()
        return None

    def nameInBinding (self):
        """Return the name by which this component is known in the generated
        binding.

        @note: To support builtin datatypes, type definitions with an
        associated L{pythonSupport<SimpleTypeDefinition.pythonSupport>} class
        initialize their binding name from the class name when the support
        association is created.  As long as no built-in datatype conflicts
        with a language keyword, this should be fine."""
        return self.__nameInBinding

    def hasBinding (self):
        """Return C{True} iff this is a component which has a user-visible
        Python construct which serves as its binding.

        Type definitions have classes as their bindings.  Global element
        declarations have instances of L{pyxb.binding.basis.element} as their
        bindings."""
        return self.isTypeDefinition() or (isinstance(self, ElementDeclaration) and self._scopeIsGlobal())

    def setNameInBinding (self, name_in_binding):
        """Set the name by which this component shall be known in the XSD binding."""
        self.__nameInBinding = name_in_binding
        return self

    def _updateFromOther_csc (self, other):
        """Override fields in this instance with those from the other.

        Post-extended; description in leaf implementation in
        ComplexTypeDefinition and SimpleTypeDefinition."""
        assert self != other
        self_fn = lambda *_args, **_kw: self
        getattr(super(_SchemaComponent_mixin, self), '_updateFromOther_csc', self_fn)(other)
        # The only thing we update is the binding name, and that only if it's new.
        if self.__nameInBinding is None:
            self.__nameInBinding = other.__nameInBinding
        return self

    def schemaOrderSortKey (self):
        """A key to be used when sorting components for binding generation.

        This is a tuple comprising the namespace URI, schema location, and
        line and column of the component definition within the schema.  The
        purpose is to ensure consistent order of binding components in
        generated code, to simplify maintenance involving the generated
        sources.

        To support Python 3 values that are C{None} are replaced with the
        default value for whatever type belongs in the corresponding
        position: (uri:str, locbase:str, locline:int, loccol:int) """
        if self.__schemaOrderSortKey is None:
            ns = None
            if isinstance(self, _NamedComponent_mixin):
                ns = self.bindingNamespace()
                if ns is None:
                    ns = self._namespaceContext().targetNamespace()
            elif isinstance(self, _ParticleTree_mixin):
                ns = self._namespaceContext().targetNamespace()
            ns_uri = ''
            if (ns is not None) and (ns.uri() is not None):
                ns_uri = ns.uri()
            key_elts = [ns_uri]
            loc = self._location()
            v = ''
            if (loc is not None) and (loc.locationBase is not None):
                v = loc.locationBase
            key_elts.append(v)
            v = 0
            if (loc is not None) and (loc.lineNumber is not None):
                v = loc.lineNumber
            key_elts.append(v)
            v = 0
            if (loc is not None) and (loc.columnNumber is not None):
                v = loc.columnNumber
            key_elts.append(v)
            self.__schemaOrderSortKey = tuple(key_elts)
        return self.__schemaOrderSortKey
    __schemaOrderSortKey = None

    def facStateSortKey (self):
        """A sort key matching preferred content order.

        This is an ordinal (integer) used to control which candidate
        transitions are attempted first when testing symbols against the
        content automaton state.

        @note: The value associated with a node (especially a L{ModelGroup} or
        L{Particle} will be different for different complex types, and is
        valid only during generation of the automata code for a given type."""
        assert self.__facStateSortKey is not None
        return self.__facStateSortKey

    def _setFacStateSortKey (self, key):
        """Set the automata state sort key.

        @param key: the ordinal used for sorting."""
        self.__facStateSortKey = key
    __facStateSortKey = None
    __PrivateTransient.add('facStateSortKey')

class _ParticleTree_mixin (pyxb.cscRoot):
    def _walkParticleTree (self, visit, arg):
        """Mix-in supporting walks of L{Particle} trees.

        This invokes a provided function on each node in a tree defining the
        content model of a particle, both on the way down the tree and on the
        way back up.  A standard implementation would be::

          def _walkParticleTree (self, visit, arg):
            visit(self, True, arg)
            self.__term.walkParticleTree(visit, arg)
            visit(self, False, arg)

        @param visit: A callable with parameters C{node, entering, arg} where
        C{node} is an instance of a class inheriting L{_ParticleTree_mixin},
        C{entering} indicates tree transition status, and C{arg} is a
        caller-provided state parameter.  C{entering} is C{True} if C{node}
        has particle children and the call is before they are visited;
        C{None} if the C{node} has no particle children; and C{False} if
        C{node} has particle children and they have been visited.

        @param arg: The caller-provided state parameter to be passed along
        with the node and entry/exit status in the invocation of C{visit}.
        """
        raise NotImplementedError('%s._walkParticleTree' % (self.__class__.__name__,))

class _Singleton_mixin (pyxb.cscRoot):
    """This class is a mix-in which guarantees that only one instance
    of the class will be created.  It is used to ensure that the
    ur-type instances are pointer-equivalent even when unpickling.
    See ComplexTypeDefinition.UrTypeDefinition()."""
    def __new__ (cls, *args, **kw):
        singleton_property = '_%s__singleton' % (cls.__name__,)
        if not (singleton_property in cls.__dict__):
            setattr(cls, singleton_property, super(_Singleton_mixin, cls).__new__(cls, *args, **kw))
        return cls.__dict__[singleton_property]

class _Annotated_mixin (pyxb.cscRoot):
    """Mix-in that supports an optional single annotation that describes the component.

    Most schema components have annotations.  The ones that don't are
    L{AttributeUse}, L{Particle}, and L{Annotation}.  L{ComplexTypeDefinition}
    and L{Schema} support multiple annotations, so do not mix-in this
    class."""

    # Optional Annotation instance
    __annotation = None

    def __init__ (self, *args, **kw):
        super(_Annotated_mixin, self).__init__(*args, **kw)
        self.__annotation = kw.get('annotation')

    def _annotationFromDOM (self, node):
        cn = domutils.LocateUniqueChild(node, 'annotation')
        if cn is not None:
            kw = { }
            if isinstance(self, _SchemaComponent_mixin):
                kw['owner'] = self
            self.__annotation = Annotation.CreateFromDOM(cn, **kw)

    def _updateFromOther_csc (self, other):
        """Override fields in this instance with those from the other.

        Post-extended; description in leaf implementation in
        ComplexTypeDefinition and SimpleTypeDefinition."""
        assert self != other
        self_fn = lambda *_args, **_kw: self
        getattr(super(_Annotated_mixin, self), '_updateFromOther_csc', self_fn)(other)
        # @todo: make this a copy?
        self.__annotation = other.__annotation
        return self

    def annotation (self):
        return self.__annotation

class _PickledAnonymousReference (object):
    """A helper that encapsulates a reference to an anonymous type in a different namespace.

    Normally references to components in other namespaces can be made using
    the component's name.  This is not the case when a namespace derives from
    a base type in another namespace and needs to reference the attribute or
    element declarations held in that type.  If these declarations are local
    to the base complex type, they cannot be identified by name.  This class
    provides a pickleable representation for them that behaves rather like an
    L{pyxb.namespace.ExpandedName} instance in that it can be used to
    dereference various component types."""

    __AnonymousCategory = pyxb.namespace.archive.NamespaceArchive._AnonymousCategory()

    __namespace = None
    __anonymousName = None
    def __init__ (self, namespace, anonymous_name):
        """Create a new anonymous reference.

        @param namespace: The namespace in which the component is declared.
        @type namespace: L{pyxb.namespace.Namespace}
        @param anonymous_name: A generated name guaranteed to be unique within
        the namespace.  See L{_NamedComponent_mixin._anonymousName}.
        @type anonymous_name: C{basestring}.
        """
        self.__namespace = namespace
        self.__anonymousName = anonymous_name
        assert self.__anonymousName is not None

    @classmethod
    def FromPickled (cls, object_reference):
        """Return the component referred to by the provided reference,
        regardless of whether it is a normal or anonymous reference."""
        if not isinstance(object_reference, _PickledAnonymousReference):
            assert isinstance(object_reference, tuple)
            object_reference = pyxb.namespace.ExpandedName(object_reference)
        return object_reference

    def namespace (self):
        return self.__namespace

    def anonymousName (self):
        return self.__anonymousName

    def validateComponentModel (self):
        """Forward to the associated namespace."""
        return self.__namespace.validateComponentModel()

    def __lookupObject (self):
        return self.__namespace.categoryMap(self.__AnonymousCategory).get(self.__anonymousName)

    typeDefinition = __lookupObject
    attributeGroupDefinition = __lookupObject
    modelGroupDefinition = __lookupObject
    attributeDeclaration = __lookupObject
    elementDeclaration = __lookupObject
    identityConstraintDefinition = __lookupObject
    notationDeclaration = __lookupObject

    def __str__ (self):
        """Represent the anonymous reference in a form recognizable by a developer."""
        return 'ANONYMOUS:%s' % (pyxb.namespace.ExpandedName(self.__namespace, self.__anonymousName),)

class _NamedComponent_mixin (pyxb.utils.utility.PrivateTransient_mixin, pyxb.cscRoot):
    """Mix-in to hold the name and targetNamespace of a component.

    The name may be None, indicating an anonymous component.  The
    targetNamespace is never None, though it could be an empty namespace.  The
    name and targetNamespace values are immutable after creation.

    This class overrides the pickling behavior: when pickling a Namespace,
    objects that do not belong to that namespace are pickled as references,
    not as values.  This ensures the uniqueness of objects when multiple
    namespace definitions are pre-loaded.

    This class must follow L{_SchemaComponent_mixin} in the MRO.
    """

    __PrivateTransient = set()

    def name (self):
        """Name of the component within its scope or namespace.

        This is an NCName.  The value isNone if the component is
        anonymous.  The attribute is immutable after the component is
        created creation."""
        return self.__name
    __name = None

    def isAnonymous (self):
        """Return true iff this instance is locally scoped (has no name)."""
        return self.__name is None

    def _setAnonymousName (self, namespace, unique_id=None, anon_name=None):
        # If this already has a name, keep using it.
        if self.__anonymousName is not None:
            return
        assert self.__needAnonymousSupport()
        assert namespace is not None
        if self.bindingNamespace() is not None:
            assert self.bindingNamespace() == namespace
        if self.targetNamespace() is not None:
            assert self.targetNamespace() == namespace
        if anon_name is None:
            anon_name = self.nameInBinding()
            if anon_name is None:
                anon_name = self.name()
            if anon_name is None:
                anon_name = 'ANON_IN_GROUP'
            if unique_id is not None:
                anon_name = '%s_%s' % (anon_name, unique_id)
            anon_name = pyxb.utils.utility.MakeUnique(anon_name, set(six.iterkeys(namespace.categoryMap(self.__AnonymousCategory))))
        self.__anonymousName = anon_name
        namespace.addCategoryObject(self.__AnonymousCategory, anon_name, self)
    def _anonymousName (self, namespace=None):
        assert self.__anonymousName is not None, '%x %s %s in %s missing anonymous name' % (id(self), type(self), self.name(), self.targetNamespace())
        return self.__anonymousName
    __anonymousName = None

    def targetNamespace (self):
        """The targetNamespace of a component.

        This is None, or a reference to a Namespace in which the
        component is declared (either as a global or local to one of
        the namespace's complex type definitions).  This is immutable
        after creation.
        """
        return self.__targetNamespace
    __targetNamespace = None

    def bindingNamespace (self):
        """The namespace in which this component's binding is placed."""
        return self.__bindingNamespace
    def _setBindingNamespace (self, namespace):
        self.__bindingNamespace = namespace
    __bindingNamespace = None

    def _templateMap (self):
        """A map from template keys to component-specific values.

        This is used in code generation to maintain unique names for accessor
        methods, identifiers, keys, and other characteristics associated with
        the code generated in support of the binding for this component."""
        return self.__templateMap
    __templateMap = None

    __AnonymousCategory = pyxb.namespace.archive.NamespaceArchive._AnonymousCategory()

    def __needAnonymousSupport (self):
        # If this component doesn't have a name, or if it's in some scope in
        # which it cannot be located in a category map, we'll need a unique
        # name for it.
        return self.isAnonymous() or (self._scopeIsIndeterminate() and not isinstance(self, (AttributeGroupDefinition, ModelGroupDefinition)))

    def _schema (self):
        """Return the schema component from which this component was defined.

        Needed so we can distinguish components that came from different
        locations, since that imposes an external order dependency on them and
        on cross-namespace inclusions.

        @note: This characteristic is removed when the component is stored in
        a namespace archive."""
        return self.__schema
    __schema = None
    __PrivateTransient.add('schema')

    def _prepareForArchive_csc (self, module_record):
        if self.__needAnonymousSupport():
            self._setAnonymousName(module_record.namespace(), unique_id=module_record.generationUID())
        self_fn = lambda *_args, **_kw: self
        return getattr(super(_NamedComponent_mixin, self), '_prepareForArchive_csc', self_fn)(module_record)

    def _picklesInArchive (self, archive):
        """Return C{True} if this component should be pickled by value in the
        given namespace.

        When pickling, a declaration component is considered to belong to the
        namespace if it has a local scope which belongs to the namespace.  In
        that case, the declaration is a clone of something that does not
        belong to the namespace; but the clone does.

        @see: L{_bindsInNamespace}

        @return: C{False} if the component should be pickled by reference.
        """
        if isinstance(self._scope(), ComplexTypeDefinition):
            return self._scope()._picklesInArchive(archive)
        assert not (self.targetNamespace() is None), '%s has no tns, scope %s, location %s, schema %s' % (self, self._scope(), self._location(), self._schema().targetNamespace())
        assert not (self._objectOrigin() is None)
        new_flag = (self._objectOrigin().generationUID() == archive.generationUID())
        return new_flag

    def _bindsInNamespace (self, ns):
        """Return C{True} if the binding for this component should be
        generated in the given namespace.

        This is the case when the component is in the given namespace.  It's
        also the case when the component has no associated namespace (but not
        an absent namespace).  Be aware that cross-namespace inheritance means
        you will get references to elements in another namespace when
        generating code for a subclass; that's fine, and those references
        should not be generated locally.
        """
        return self.targetNamespace() in (ns, None)

    def expandedName (self):
        """Return the L{pyxb.namespace.ExpandedName} of this object."""
        if self.name() is None:
            return None
        return pyxb.namespace.ExpandedName(self.targetNamespace(), self.name())

    def __new__ (cls, *args, **kw):
        """Pickling support.

        Normally, we just create a new instance of this class.
        However, if we're unpickling a reference in a loadable schema,
        we need to return the existing component instance by looking
        up the name in the component map of the desired namespace.  We
        can tell the difference because no normal constructors that
        inherit from this have positional arguments; only invocations
        by unpickling with a value returned in __getnewargs__ do.

        This does require that the dependent namespace already have
        been validated (or that it be validated here).  That shouldn't
        be a problem, except for the dependency loop resulting from
        use of xml:lang in the XMLSchema namespace.  For that issue,
        see pyxb.namespace._XMLSchema.
        """

        if 0 == len(args):
            rv = super(_NamedComponent_mixin, cls).__new__(cls)
            return rv
        ( object_reference, scope, icls ) = args

        object_reference = _PickledAnonymousReference.FromPickled(object_reference)

        # Explicitly validate here: the lookup operations won't do so,
        # but will abort if the namespace hasn't been validated yet.
        object_reference.validateComponentModel()
        rv = None
        if isinstance(scope, (tuple, _PickledAnonymousReference)):
            # Scope is the expanded name of the complex type in which the
            # named value can be located.
            scope_ref = _PickledAnonymousReference.FromPickled(scope)
            if object_reference.namespace() != scope_ref.namespace():
                scope_ref.validateComponentModel()
                assert 'typeDefinition' in scope_ref.namespace().categories()
            scope_ctd = scope_ref.typeDefinition()
            if scope_ctd is None:
                raise pyxb.SchemaValidationError('Unable to resolve local scope %s' % (scope_ref,))
            if issubclass(icls, AttributeDeclaration):
                rv = scope_ctd.lookupScopedAttributeDeclaration(object_reference)
            elif issubclass(icls, ElementDeclaration):
                rv = scope_ctd.lookupScopedElementDeclaration(object_reference)
            if rv is None:
                raise pyxb.SchemaValidationError('Unable to resolve %s as %s in scope %s' % (object_reference, icls, scope_ref))
        elif _ScopedDeclaration_mixin.ScopeIsGlobal(scope) or _ScopedDeclaration_mixin.ScopeIsIndeterminate(scope):
            if (issubclass(icls, SimpleTypeDefinition) or issubclass(icls, ComplexTypeDefinition)):
                rv = object_reference.typeDefinition()
            elif issubclass(icls, AttributeGroupDefinition):
                rv = object_reference.attributeGroupDefinition()
            elif issubclass(icls, ModelGroupDefinition):
                rv = object_reference.modelGroupDefinition()
            elif issubclass(icls, AttributeDeclaration):
                rv = object_reference.attributeDeclaration()
            elif issubclass(icls, ElementDeclaration):
                rv = object_reference.elementDeclaration()
            elif issubclass(icls, IdentityConstraintDefinition):
                rv = object_reference.identityConstraintDefinition()
            if rv is None:
                raise pyxb.SchemaValidationError('Unable to resolve %s as %s' % (object_reference, icls))
        if rv is None:
            raise pyxb.SchemaValidationError('Unable to resolve reference %s, scope %s ns %s type %s, class %s' % (object_reference, scope, (scope is None and "<unknown>" or scope.targetNamespace()), type(scope), icls))
        return rv

    def __init__ (self, *args, **kw):
        assert 0 == len(args)
        name = kw.get('name')
        # Must be None or a valid NCName
        assert (name is None) or (0 > name.find(':')), 'name %s' % (name,)
        self.__name = name

        # Target namespace is taken from the context, unless somebody
        # overrides it (as is done for local declarations if the form is
        # unqualified).
        self.__targetNamespace = kw.get('target_namespace', self._namespaceContext().targetNamespace())
        self.__bindingNamespace = kw.get('binding_namespace')

        self.__templateMap = {}

        self.__schema = kw.get('schema')
        assert self._schema() is not None

        # Do parent invocations after we've set the name: they might need it.
        super(_NamedComponent_mixin, self).__init__(*args, **kw)

    def isNameEquivalent (self, other):
        """Return true iff this and the other component share the same name and target namespace.

        Anonymous components are inherently name inequivalent, except to
        themselves.  This relies on equivalence as defined for
        pyxb.namespace.ExpandedName, for which None is not equivalent to any
        non-anonymous name."""
        # Note that unpickled objects
        return (self == other) or ((not self.isAnonymous()) and (self.expandedName() == other.expandedName()))

    def isTypeEquivalent (self, other):
        """Return True iff this and the other component have matching types.

        It appears that name equivalence is used; two complex type definitions
        with identical structures are not considered equivalent (at least, per
        XMLSpy).
        """
        return (type(self) == type(other)) and self.isNameEquivalent(other)

    def isDerivationConsistent (self, other):
        """Return True iff this type can serve as a restriction of the other
        type for the purposes of U{element consistency<http://www.w3.org/TR/xmlschema-1/#cos-element-consistent>}.

        It appears that name equivalence is normally used; two complex type
        definitions with identical structures are not considered equivalent
        (at least, per XMLSpy).  However, some OpenGIS standards demonstrate
        that derivation by restriction from the other type is also acceptable.
        That opens a whole can of worms; see
        L{ElementDeclaration.isAdaptable}.
        """
        this = self
        # can this succeed if component types are not equivalent?
        while this is not None:
            if this.isTypeEquivalent(other):
                return True
            # Assumption from ElementDeclaration.isAdaptable
            assert this.isResolved() and other.isResolved()
            if isinstance(self, ComplexTypeDefinition):
                if self.DM_restriction != this.derivationMethod():
                    return False
            else:
                assert isinstance(self, SimpleTypeDefinition)
                if self._DA_restriction != this._derivationAlternative():
                    return False
                if not this.baseTypeDefinition().isDerivationConsistent(other):
                    return False
            this = this.baseTypeDefinition()
        return False

    def _picklingReference (self):
        if self.__needAnonymousSupport():
            assert self._anonymousName() is not None
            return _PickledAnonymousReference(self.targetNamespace(), self._anonymousName())
        return self.expandedName().uriTuple()

    def __pickleAsReference (self):
        if self.targetNamespace() is None:
            return False
        # Get the namespace we're pickling.  If the namespace is None,
        # we're not pickling; we're probably cloning, and in that case
        # we don't want to use the reference state encoding.
        pickling_archive = pyxb.namespace.archive.NamespaceArchive.PicklingArchive()
        if pickling_archive is None:
            return False
        # If this thing is scoped in a complex type that belongs to the
        # namespace being pickled, then it gets pickled as an object even if
        # its target namespace isn't this one.
        assert self._objectOrigin() is not None
        if self._picklesInArchive(pickling_archive):
            return False
        # Note that anonymous objects must use their fallback
        return True

    def __getstate__ (self):
        if self.__pickleAsReference():
            # NB: This instance may be a scoped declaration, but in
            # this case (unlike getnewargs) we don't care about trying
            # to look up a previous instance, so we don't need to
            # encode the scope in the reference tuple.
            return self._picklingReference()
        if self.targetNamespace() is None:
            # The only internal named objects that should exist are
            # ones that have a non-global scope (including those with
            # absent scope).
            # @todo: this is wrong for schema that are not bound to a
            # namespace, unless we use an unbound Namespace instance
            #assert isinstance(self, _ScopedDeclaration_mixin)
            #assert self.SCOPE_global != self.scope()
            # NOTE: The name of the scope may be None.  This is not a
            # problem unless somebody tries to extend or restrict the
            # scope type, which at the moment I'm thinking is
            # impossible for anonymous types.  If it isn't, we're
            # gonna need some other sort of ID, like a UUID associated
            # with the anonymous class at the time it's written to the
            # preprocessed schema file.
            pass
        return super(_NamedComponent_mixin, self).__getstate__()

    def __getnewargs__ (self):
        """Pickling support.

        If this instance is being pickled as a reference, provide the
        arguments that are necessary so that the unpickler can locate
        the appropriate component rather than create a duplicate
        instance."""

        if self.__pickleAsReference():
            scope = self._scope()
            if isinstance(self, _ScopedDeclaration_mixin):
                # If scope is global, we can look it up in the namespace.
                # If scope is indeterminate, this must be within a group in
                # another namespace.  Why are we serializing it?
                # If scope is local, provide the namespace and name of
                # the type that holds it
                if self.SCOPE_global == self.scope():
                    pass
                elif isinstance(self.scope(), ComplexTypeDefinition):
                    scope = self.scope()._picklingReference()
                    assert isinstance(scope, (tuple, _PickledAnonymousReference)), self
                else:
                    assert self._scopeIsIndeterminate()
                    # This is actually OK: we made sure both the scope and
                    # this instance can be looked up by a unique identifier.
            else:
                assert isinstance(self, _NamedComponent_mixin), 'Pickling unnamed component %s in indeterminate scope by reference' % (self,)
                assert not isinstance(scope, ComplexTypeDefinition), '%s %s %s %s' % (self, self.name(), scope, self._objectOrigin())

            rv = ( self._picklingReference(), scope, self.__class__ )
            return rv
        return ()

    def __setstate__ (self, state):
        if isinstance(state, tuple):
            # We don't actually have to set any state here; we just
            # make sure that we resolved to an already-configured
            # instance.
            assert self.targetNamespace() is not None
            assert self.targetNamespace().uri() == state[0]
            assert self.name() == state[1]
            return
        if isinstance(state, _PickledAnonymousReference):
            assert self.targetNamespace() is not None
            assert self.targetNamespace() == state.namespace()
            assert self.__needAnonymousSupport()
            assert self._anonymousName() == state.anonymousName()
            return
        self.__dict__.update(state)

    def _resetClone_csc (self, **kw):
        self.__schema = None
        self_fn = lambda *_args, **_kw: self
        rv = getattr(super(_NamedComponent_mixin, self), '_resetClone_csc', self_fn)(**kw)
        self.__templateMap = { }
        origin = kw.get('origin')
        self.__anonymousName = None
        self._setObjectOrigin(origin, override=True)
        return rv

class _ValueConstraint_mixin (pyxb.cscRoot):
    """Mix-in indicating that the component contains a simple-type
    value that may be constrained."""

    VC_na = 0                   #<<< No value constraint applies
    VC_default = 1              #<<< Provided value constraint is default value
    VC_fixed = 2                #<<< Provided value constraint is fixed value

    # None, or a tuple containing a string followed by one of the VC_*
    # values above.
    __valueConstraint = None
    def valueConstraint (self):
        """A constraint on the value of the attribute or element.

        Either None, or a pair consisting of a string in the lexical
        space of the typeDefinition and one of VC_default and
        VC_fixed."""
        return self.__valueConstraint

    def default (self):
        """If this instance constraints a default value, return that
        value; otherwise return None."""
        if not isinstance(self.__valueConstraint, tuple):
            return None
        if self.VC_default != self.__valueConstraint[1]:
            return None
        return self.__valueConstraint[0]

    def fixed (self):
        """If this instance constraints a fixed value, return that
        value; otherwise return None."""
        if not isinstance(self.__valueConstraint, tuple):
            return None
        if self.VC_fixed != self.__valueConstraint[1]:
            return None
        return self.__valueConstraint[0]

    def _valueConstraintFromDOM (self, node):
        adefault = domutils.NodeAttribute(node, 'default')
        afixed = domutils.NodeAttribute(node, 'fixed')
        ause = domutils.NodeAttribute(node, 'use')
        if (adefault is not None) and (afixed is not None):
            raise pyxb.SchemaValidationError('Attributes default and fixed may not both appear (3.2.3r1)')
        if adefault is not None:
            if (ause is not None) and ('optional' != ause):
                raise pyxb.SchemaValidationError('Attribute use must be optional when default present (3.2.3r2)')
            self.__valueConstraint = (adefault, self.VC_default)
            return self
        if afixed is not None:
            self.__valueConstraint = (afixed, self.VC_fixed)
            return self
        self.__valueConstraint = None
        return self

class _ScopedDeclaration_mixin (pyxb.cscRoot):
    """Mix-in class for named components that have a scope.

    Scope is important when doing cross-namespace inheritance,
    e.g. extending or restricting a complex type definition that is
    from a different namespace.  In this case, we will need to retain
    a reference to the external component when the schema is
    serialized.

    This is done in the pickling process by including the scope when
    pickling a component as a reference.  The scope is the
    SCOPE_global if global; otherwise, it is a tuple containing the
    external namespace URI and the NCName of the complex type
    definition in that namespace.  We assume that the complex type
    definition has global scope; otherwise, it should not have been
    possible to extend or restrict it.  (Should this be untrue, there
    are comments in the code about a possible solution.)

    @warning: This mix-in must follow L{_NamedComponent_mixin} in the C{mro}.
    """

    SCOPE_global = 'global'     #<<< Marker to indicate global scope
    XSCOPE_indeterminate = 'indeterminate' #<<< Marker to indicate scope has not been assigned

    @classmethod
    def IsValidScope (cls, value):
        return (cls.SCOPE_global == value) or isinstance(value, ComplexTypeDefinition)

    @classmethod
    def ScopeIsIndeterminate (cls, value):
        return (cls.XSCOPE_indeterminate == value)

    @classmethod
    def ScopeIsGlobal (cls, value):
        return (cls.SCOPE_global == value)

    def _scopeIsCompatible (self, scope):
        """Return True if this scope currently assigned to this instance is compatible with the given scope.

        If either scope is indeterminate, presume they will ultimately be
        compatible.  Scopes that are equal are compatible, as is a local scope
        if this already has a global scope."""
        if self.ScopeIsIndeterminate(scope) or self.ScopeIsIndeterminate(self.scope()):
            return True
        if self.scope() == scope:
            return True
        return (self.SCOPE_global == self.scope()) and isinstance(scope, ComplexTypeDefinition)

    # The scope for the element.  Valid values are SCOPE_global or a
    # complex type definition.  None is an invalid value, but may
    # appear if scope is determined by an ancestor component.
    def scope (self):
        """The scope for the declaration.

        Valid values are SCOPE_global, or a complex type definition.
        A value of None means a non-global declaration that is not
        owned by a complex type definition.  These can only appear in
        attribute group definitions, model group definitions, and element
        declarations.

        @todo: For declarations in named model groups (viz., local
        elements that aren't references), the scope needs to be set by
        the owning complex type.
        """
        return self._scope()

    # The base declaration is the original _ScopedDeclaration_mixin which
    # introduced the element into its scope.  This is used to retain a
    # particular defining declaration when each extension type gets its own
    # clone adapted for its scope.
    __baseDeclaration = None
    def baseDeclaration (self):
        return self.__baseDeclaration or self
    def _baseDeclaration (self, referenced_declaration):
        self.__baseDeclaration = referenced_declaration.baseDeclaration()
        return self.__baseDeclaration

class _AttributeWildcard_mixin (pyxb.cscRoot):
    """Support for components that accept attribute wildcards.

    That is L{AttributeGroupDefinition} and L{ComplexTypeDefinition}.  The
    calculations of the appropriate wildcard are sufficiently complex that
    they need to be abstracted out to a mix-in class."""

    # Optional wildcard that constrains attributes
    __attributeWildcard = None

    def attributeWildcard (self):
        """Return the L{Wildcard} component associated with attributes of this
        instance, or C{None} if attribute wildcards are not present in the
        instance."""
        return self.__attributeWildcard

    def _setAttributeWildcard (self, attribute_wildcard):
        """Set the attribute wildcard property for this instance."""
        assert (attribute_wildcard is None) or isinstance(attribute_wildcard, Wildcard)
        self.__attributeWildcard = attribute_wildcard
        return self

    def _attributeRelevantChildren (self, node_list):
        """Return the nodes that are relevant for attribute processing.

        @param node_list: A sequence of nodes found in a definition content
        information item.

        @return: A tuple C{( attributes, attributeGroups, attributeWildcard)}
        where C{attributes} is the subsequence of C{node_list} that are
        XMLSchema C{attribute} nodes; C{attributeGroups} is analogous; and
        C{attributeWildcard} is a single DOM node with XMLSchema name
        C{anyAttribute} (or C{None}, if no such node is present in the list).

        @raise pyxb.SchemaValidationError: An C{attributeGroup} node is
        present but does not have the required C{ref} attribute.
        @raise pyxb.SchemaValidationError: Multiple C{anyAttribute} nodes are
        identified.
        """

        attributes = []
        attribute_groups = []
        any_attribute = None
        # Handle clauses 1 and 2 (common between simple and complex types)
        for node in node_list:
            if Node.ELEMENT_NODE != node.nodeType:
                continue
            if xsd.nodeIsNamed(node, 'attribute'):
                # Note: This attribute use instance may have use=prohibited
                attributes.append(node)
            elif xsd.nodeIsNamed(node, 'attributeGroup'):
                # This must be an attributeGroupRef
                agd_en = domutils.NodeAttributeQName(node, 'ref')
                if agd_en is None:
                    raise pyxb.SchemaValidationError('Require ref attribute on internal attributeGroup elements')
                attribute_groups.append(agd_en)
            elif xsd.nodeIsNamed(node, 'anyAttribute'):
                if any_attribute is not None:
                    raise pyxb.SchemaValidationError('Multiple anyAttribute children are not allowed')
                any_attribute = node

        return (attributes, attribute_groups, any_attribute)

    @classmethod
    def CompleteWildcard (cls, namespace_context, attribute_groups, local_wildcard):
        """Implement the algorithm as described the
        U{specification<http://www.w3.org/TR/xmlschema-1/#declare-type>}.

        @param namespace_context: The L{pyxb.namespace.NamespaceContext} to be
        associated with any created L{Wildcard} instance
        @param attribute_groups: A list of L{AttributeGroupDefinition} instances
        @param local_wildcard: A L{Wildcard} instance computed from a relevant
        XMLSchema C{anyAttribute} element, or C{None} if no attribute wildcard
        is relevant
        """

        # Non-absent wildcard properties of attribute groups
        agd_wildcards = []
        for agd in attribute_groups:
            assert isinstance(agd, AttributeGroupDefinition)
            if agd.attributeWildcard() is not None:
                agd_wildcards.append(agd.attributeWildcard())
        agd_constraints = [ _agd.namespaceConstraint() for _agd in agd_wildcards ]

        # Clause 2.1
        if 0 == len(agd_wildcards):
            return local_wildcard

        if local_wildcard is not None:
            # Clause 2.2.1
            return Wildcard(process_contents=local_wildcard.processContents(),
                            namespace_constraint=Wildcard.IntensionalIntersection(agd_constraints + [local_wildcard.namespaecConstraint()]),
                            annotation=local_wildcard.annotation(),
                            namespace_context=namespace_context)
        # Clause 2.2.2
        return Wildcard(process_contents=agd_wildcards[0].processContents(),
                        namespace_constraint=Wildcard.IntensionalIntersection(agd_constraints),
                        namespace_context=namespace_context)

class AttributeDeclaration (_SchemaComponent_mixin, _NamedComponent_mixin, pyxb.namespace.resolution._Resolvable_mixin, _Annotated_mixin, _ValueConstraint_mixin, _ScopedDeclaration_mixin):
    """An XMLSchema U{Attribute Declaration<http://www.w3.org/TR/xmlschema-1/#cAttribute_Declarations>} component.
    """

    # The STD to which attribute values must conform
    __typeDefinition = None
    def typeDefinition (self):
        """The simple type definition to which an attribute value must
         conform."""
        return self.__typeDefinition

    # The expanded name content of the XSD type attribute
    __typeExpandedName = None

    def __init__ (self, *args, **kw):
        super(AttributeDeclaration, self).__init__(*args, **kw)
        assert 'scope' in kw

    def __str__ (self):
        if self.typeDefinition():
            return 'AD[%s:%s]' % (self.name(), self.typeDefinition().expandedName())
        return 'AD[%s:?]' % (self.expandedName(),)

    @classmethod
    def CreateBaseInstance (cls, name, schema, std=None):
        """Create an attribute declaration component for a specified namespace."""
        kw = { 'name' : name,
               'schema' : schema,
               'namespace_context' : schema.targetNamespace().initialNamespaceContext(),
               'scope' : _ScopedDeclaration_mixin.SCOPE_global }
        assert schema is not None
        bi = cls(**kw)
        if std is not None:
            bi.__typeDefinition = std
        bi.__typeExpandedName = None
        return bi

    # CFD:AD CFD:AttributeDeclaration
    @classmethod
    def CreateFromDOM (cls, node, **kw):
        """Create an attribute declaration from the given DOM node.

        wxs is a Schema instance within which the attribute is being
        declared.

        node is a DOM element.  The name must be one of ( 'all',
        'choice', 'sequence' ), and the node must be in the XMLSchema
        namespace.

        scope is the _ScopeDeclaration_mxin context into which the
        attribute declaration is placed.  It can be SCOPE_global, a
        complex type definition, or XSCOPE_indeterminate if this is an
        anonymous declaration within an attribute group.  It is a
        required parameter for this function.
        """

        scope = kw['scope']
        assert _ScopedDeclaration_mixin.ScopeIsIndeterminate(scope) or _ScopedDeclaration_mixin.IsValidScope(scope)

        # Node should be an XMLSchema attribute node
        assert xsd.nodeIsNamed(node, 'attribute')

        name = domutils.NodeAttribute(node, 'name')

        # Implement per section 3.2.2
        if xsd.nodeIsNamed(node.parentNode, 'schema'):
            assert cls.SCOPE_global == scope
        elif domutils.NodeAttribute(node, 'ref') is None:
            # This is an anonymous declaration within an attribute use
            assert _ScopedDeclaration_mixin.ScopeIsIndeterminate(scope) or isinstance(scope, ComplexTypeDefinition)
        else:
            raise pyxb.SchemaValidationError('Internal attribute declaration by reference')

        rv = cls(name=name, node=node, **kw)
        rv._annotationFromDOM(node)
        rv._valueConstraintFromDOM(node)

        rv.__typeExpandedName = domutils.NodeAttributeQName(node, 'type')

        kw.pop('node', None)
        kw['owner'] = rv

        st_node = domutils.LocateUniqueChild(node, 'simpleType')
        if st_node is not None:
            rv.__typeDefinition = SimpleTypeDefinition.CreateFromDOM(st_node, **kw)
        elif rv.__typeExpandedName is None:
            rv.__typeDefinition = SimpleTypeDefinition.SimpleUrTypeDefinition()

        if rv.__typeDefinition is None:
            rv._queueForResolution('creation')
        return rv

    def isResolved (self):
        return self.__typeDefinition is not None

    # res:AD res:AttributeDeclaration
    def _resolve (self):
        if self.isResolved():
            return self

        # Although the type definition may not be resolved, *this* component
        # is resolved, since we don't look into the type definition for anything.
        assert self.__typeExpandedName is not None, 'AD %s is unresolved but had no type attribute field' % (self.expandedName(),)
        self.__typeDefinition = self.__typeExpandedName.typeDefinition()
        if self.__typeDefinition is None:
            raise pyxb.SchemaValidationError('Type reference %s cannot be found' % (self.__typeExpandedName,))
        if not isinstance(self.__typeDefinition, SimpleTypeDefinition):
            raise pyxb.SchemaValidationError('Need %s to be a simple type' % (self.__typeExpandedName,))

        return self

    def _updateFromOther_csc (self, other):
        """Override fields in this instance with those from the other.

        This method is invoked only by Schema._addNamedComponent, and
        then only when a built-in type collides with a schema-defined
        type.  Material like facets is not (currently) held in the
        built-in copy, so the DOM information is copied over to the
        built-in STD, which is subsequently re-resolved.

        Returns self.
        """
        assert self != other
        assert self.name() is not None
        assert self.isNameEquivalent(other)
        super(AttributeDeclaration, self)._updateFromOther_csc(other)

        # The other STD should be an unresolved schema-defined type.
        # Mark this instance as unresolved so it is re-examined
        if not other.isResolved():
            if pyxb.namespace.BuiltInObjectUID == self._objectOrigin().generationUID():
                #assert self.isResolved(), 'Built-in %s is not resolved' % (self.expandedName(),)
                _log.warning('Not destroying builtin %s: %s', self.expandedName(), self.__typeDefinition)
            else:
                self.__typeDefinition = None
        return self

    # bR:AD
    def _bindingRequires_vx (self, include_lax):
        """Attribute declarations require their type."""
        return frozenset([ self.__typeDefinition ])

class AttributeUse (_SchemaComponent_mixin, pyxb.namespace.resolution._Resolvable_mixin, _ValueConstraint_mixin):
    """An XMLSchema U{Attribute Use<http://www.w3.org/TR/xmlschema-1/#cAttribute_Use>} component."""

    # How this attribute can be used.  The component property
    # "required" is true iff the value is USE_required.
    __use = None

    USE_required = 0x01         #<<< The attribute is required
    USE_optional = 0x02         #<<< The attribute may or may not appear
    USE_prohibited = 0x04       #<<< The attribute must not appear

    def required (self):
        return self.USE_required == self.__use

    def prohibited (self):
        return self.USE_prohibited == self.__use

    # The expanded name value of the XSD ref attribute
    __refExpandedName = None

    __restrictionOf = None
    def restrictionOf (self):
        return self.__restrictionOf
    def _setRestrictionOf (self, au):
        assert isinstance(au, AttributeUse)
        # Might re-assign if had to suspend resolution
        assert (self.__restrictionOf is None) or (self.__restrictionOf == au)
        self.__restrictionOf = au

    # A reference to an AttributeDeclaration
    def attributeDeclaration (self):
        """The attribute declaration for this use.

        When the use scope is assigned, the declaration is cloned (if
        necessary) so that each declaration corresponds to only one use.  We
        rely on this in code generation, because the template map for the use
        is stored in its declaration."""
        return self.__attributeDeclaration
    __attributeDeclaration = None

    # Define so superclasses can take keywords
    def __init__ (self, **kw):
        super(AttributeUse, self).__init__(**kw)

    def matchingQNameMembers (self, au_set):
        """Return the subset of au_set for which the use names match this use."""

        if not self.isResolved():
            return None
        this_ad = self.attributeDeclaration()
        rv = set()
        for au in au_set:
            if not au.isResolved():
                return None
            that_ad = au.attributeDeclaration()
            if this_ad.isNameEquivalent(that_ad):
                rv.add(au)
        return rv

    @classmethod
    def CreateBaseInstance (cls, schema, attribute_declaration, use=USE_optional):
        kw = { 'schema' : schema,
               'namespace_context' : schema.targetNamespace().initialNamespaceContext() }
        bi = cls(**kw)
        assert isinstance(attribute_declaration, AttributeDeclaration)
        bi.__attributeDeclaration = attribute_declaration
        bi.__use = use
        return bi

    # CFD:AU CFD:AttributeUse
    @classmethod
    def CreateFromDOM (cls, node, **kw):
        """Create an Attribute Use from the given DOM node.

        wxs is a Schema instance within which the attribute use is
        being defined.

        node is a DOM element.  The name must be 'attribute', and the
        node must be in the XMLSchema namespace.

        scope is the _ScopeDeclaration_mixin context into which any
        required anonymous attribute declaration is put.  This must be
        a complex type definition, or None if this use is in an
        attribute group.
        """

        scope = kw['scope']
        assert _ScopedDeclaration_mixin.ScopeIsIndeterminate(scope) or isinstance(scope, ComplexTypeDefinition)
        assert xsd.nodeIsNamed(node, 'attribute')
        schema = kw['schema']
        rv = cls(node=node, **kw)

        rv.__use = cls.USE_optional
        use = domutils.NodeAttribute(node, 'use')
        if use is not None:
            if 'required' == use:
                rv.__use = cls.USE_required
            elif 'optional' == use:
                rv.__use = cls.USE_optional
            elif 'prohibited' == use:
                rv.__use = cls.USE_prohibited
            else:
                raise pyxb.SchemaValidationError('Unexpected value %s for attribute use attribute' % (use,))

        rv._valueConstraintFromDOM(node)

        rv.__refExpandedName = domutils.NodeAttributeQName(node, 'ref')
        if rv.__refExpandedName is None:
            # Create an anonymous declaration
            kw.pop('node', None)
            kw['owner'] = rv
            kw['target_namespace'] = schema.targetNamespaceForNode(node, AttributeDeclaration)
            rv.__attributeDeclaration = AttributeDeclaration.CreateFromDOM(node, **kw)

        if not rv.isResolved():
            rv._queueForResolution('creation')

        return rv

    def isResolved (self):
        return self.__attributeDeclaration is not None

    def _resolve (self):
        if self.isResolved():
            return self
        self.__attributeDeclaration = self.__refExpandedName.attributeDeclaration()
        if self.__attributeDeclaration is None:
            raise pyxb.SchemaValidationError('Attribute declaration %s cannot be found' % (self.__refExpandedName,))

        assert isinstance(self.__attributeDeclaration, AttributeDeclaration)

        return self

    # bR:AU
    def _bindingRequires_vx (self, include_lax):
        """Attribute uses require their declarations, but only if lax."""
        if not include_lax:
            return frozenset()
        return frozenset([ self.attributeDeclaration() ])

    # aFS:AU
    def _adaptForScope (self, ctd):
        """Adapt this instance for the given complex type.

        If the attribute declaration for this use is not associated with a
        complex type definition, then associate a clone of it with this CTD,
        and clone a new attribute use that uses the associated declaration.
        This attribute use is then inherited by extensions and restrictions,
        while retaining its original scope."""
        rv = self
        assert self.isResolved()
        ad = self.__attributeDeclaration
        assert ad.scope() is not None
        assert isinstance(ctd, ComplexTypeDefinition)
        if not isinstance(ad.scope(), ComplexTypeDefinition):
            rv = self._clone(ctd, ctd._objectOrigin())
            rv.__attributeDeclaration = ad._clone(rv, ctd._objectOrigin())
            rv.__attributeDeclaration._setScope(ctd)
        ctd._recordLocalDeclaration(rv.__attributeDeclaration)
        return rv

    def __str__ (self):
        return 'AU[%s]' % (self.attributeDeclaration(),)


class ElementDeclaration (_ParticleTree_mixin, _SchemaComponent_mixin, _NamedComponent_mixin, pyxb.namespace.resolution._Resolvable_mixin, _Annotated_mixin, _ValueConstraint_mixin, _ScopedDeclaration_mixin):
    """An XMLSchema U{Element Declaration<http://www.w3.org/TR/xmlschema-1/#cElement_Declarations>} component."""

    # Simple or complex type definition
    __typeDefinition = None
    def typeDefinition (self):
        """The simple or complex type to which the element value conforms."""
        return self.__typeDefinition
    def _typeDefinition (self, type_definition):
        self.__typeDefinition = type_definition
        if (type_definition is not None) and (self.valueConstraint() is not None):
            failed = True
            if isinstance(self.__typeDefinition, SimpleTypeDefinition):
                failed = False
            elif isinstance(self.__typeDefinition, ComplexTypeDefinition):
                # The corresponding type may not be resolved so we can't check
                # its contentType, but we should know whether it could be
                # complex.
                ct = type_definition.contentType()
                if ct is None:
                    if False == self.__typeDefinition._isComplexContent():
                        failed = False
                    else:
                        _log.error('Unable to check value constraint on %s due to incomplete resolution of type', self.expandedName())
                else:
                    failed = not (isinstance(ct, tuple) and (ComplexTypeDefinition.CT_SIMPLE == ct[0]))
            if failed:
                if self.__typeExpandedName is None:
                    raise pyxb.SchemaValidationError('Value constraint on element %s with non-simple content' % (self.expandedName(),))
                raise pyxb.SchemaValidationError('Value constraint on element %s with non-simple type %s' % (self.expandedName(), self.__typeExpandedName))
        return self

    __substitutionGroupExpandedName = None

    __typeExpandedName = None

    __nillable = False
    def nillable (self):
        return self.__nillable

    __identityConstraintDefinitions = None
    def identityConstraintDefinitions (self):
        """A list of IdentityConstraintDefinition instances."""
        return self.__identityConstraintDefinitions

    __substitutionGroupAffiliation = None
    def substitutionGroupAffiliation (self):
        """None, or a reference to an ElementDeclaration."""
        return self.__substitutionGroupAffiliation

    SGE_none = 0                #<<< No substitution group exclusion specified
    SGE_extension = 0x01        #<<< Substitution by an extension of the base type
    SGE_restriction = 0x02      #<<< Substitution by a restriction of the base type
    SGE_substitution = 0x04     #<<< Substitution by replacement (?)

    _SGE_Map = { 'extension' : SGE_extension
               , 'restriction' : SGE_restriction }
    _DS_Map = _SGE_Map.copy()
    _DS_Map.update( { 'substitution' : SGE_substitution } )

    # Subset of SGE marks formed by bitmask.  SGE_substitution is disallowed.
    __substitutionGroupExclusions = SGE_none

    # Subset of SGE marks formed by bitmask
    __disallowedSubstitutions = SGE_none

    __abstract = False
    def abstract (self):
        return self.__abstract

    def hasWildcardElement (self):
        """Return False, since element declarations are not wildcards."""
        return False

    # bR:ED
    def _bindingRequires_vx (self, include_lax):
        """Element declarations depend on the type definition of their
        content."""
        return frozenset([self.__typeDefinition])

    def __init__ (self, *args, **kw):
        super(ElementDeclaration, self).__init__(*args, **kw)

    # CFD:ED CFD:ElementDeclaration
    @classmethod
    def CreateFromDOM (cls, node, **kw):
        """Create an element declaration from the given DOM node.

        wxs is a Schema instance within which the element is being
        declared.

        scope is the _ScopeDeclaration_mixin context into which the
        element declaration is recorded.  It can be SCOPE_global, a
        complex type definition, or None in the case of elements
        declared in a named model group.

        node is a DOM element.  The name must be 'element', and the
        node must be in the XMLSchema namespace."""

        scope = kw['scope']
        assert _ScopedDeclaration_mixin.ScopeIsIndeterminate(scope) or _ScopedDeclaration_mixin.IsValidScope(scope)

        # Node should be an XMLSchema element node
        assert xsd.nodeIsNamed(node, 'element')

        # Might be top-level, might be local
        name = domutils.NodeAttribute(node, 'name')
        if xsd.nodeIsNamed(node.parentNode, 'schema'):
            assert _ScopedDeclaration_mixin.SCOPE_global == scope
        elif domutils.NodeAttribute(node, 'ref') is None:
            # Scope may be None or a CTD.
            assert _ScopedDeclaration_mixin.ScopeIsIndeterminate(scope) or isinstance(scope, ComplexTypeDefinition)
        else:
            raise pyxb.SchemaValidationError('Created reference as element declaration')

        rv = cls(name=name, node=node, **kw)
        rv._annotationFromDOM(node)
        rv._valueConstraintFromDOM(node)

        rv.__substitutionGroupExpandedName = domutils.NodeAttributeQName(node, 'substitutionGroup')

        kw.pop('node', None)
        kw['owner'] = rv

        # Global EDs should be given indeterminate scope to ensure subordinate
        # declarations are not inappropriately associated with the element's
        # namespace.  If the ED is within a non-global scope that scope should
        # be retained.
        if rv._scopeIsGlobal():
            kw['scope'] = _ScopedDeclaration_mixin.XSCOPE_indeterminate

        identity_constraints = []
        for cn in node.childNodes:
            if (Node.ELEMENT_NODE == cn.nodeType) and xsd.nodeIsNamed(cn, 'key', 'unique', 'keyref'):
                identity_constraints.append(IdentityConstraintDefinition.CreateFromDOM(cn, **kw))
        rv.__identityConstraintDefinitions = identity_constraints

        rv.__typeDefinition = None
        rv.__typeExpandedName = domutils.NodeAttributeQName(node, 'type')
        simpleType_node = domutils.LocateUniqueChild(node, 'simpleType')
        complexType_node = domutils.LocateUniqueChild(node, 'complexType')
        if rv.__typeExpandedName is not None:
            if (simpleType_node is not None) and (complexType_node is not None):
                raise pyxb.SchemaValidationError('Cannot combine type attribute with simpleType or complexType child')
        if (rv.__typeDefinition is None) and (simpleType_node is not None):
            rv._typeDefinition(SimpleTypeDefinition.CreateFromDOM(simpleType_node, **kw))
        if (rv.__typeDefinition is None) and (complexType_node is not None):
            rv._typeDefinition(ComplexTypeDefinition.CreateFromDOM(complexType_node, **kw))
        if rv.__typeDefinition is None:
            if rv.__typeExpandedName is None:
                # Scan for particle types which were supposed to be enclosed in a complexType
                for cn in node.childNodes:
                    if Particle.IsParticleNode(cn):
                        raise pyxb.SchemaValidationError('Node %s in element must be wrapped by complexType.' % (cn.localName,))
                rv._typeDefinition(ComplexTypeDefinition.UrTypeDefinition())
        rv.__isResolved = (rv.__typeDefinition is not None) and (rv.__substitutionGroupExpandedName is None)
        if not rv.__isResolved:
            rv._queueForResolution('creation')

        attr_val = domutils.NodeAttribute(node, 'nillable')
        if attr_val is not None:
            rv.__nillable = datatypes.boolean(attr_val)

        attr_val = domutils.NodeAttribute(node, 'abstract')
        if attr_val is not None:
            rv.__abstract = datatypes.boolean(attr_val)

        schema = kw['schema']
        rv.__disallowedSubstitutions = schema.blockForNode(node, cls._DS_Map)
        rv.__substitutionGroupExclusions = schema.finalForNode(node, cls._SGE_Map)

        return rv

    def isAdaptable (self, ctd):
        """Determine whether this element declaration is adaptable.

        OK, this gets ugly.  First, if this declaration isn't resolved, it's
        clearly not adaptable.

        Now: For it to be adaptable, we must know enough about its type to
        verify that it is derivation-consistent with any other uses of the
        same name in the same complex type.  If the element's type is
        resolved, that's good enough.

        If the element's type isn't resolved, we're golden as long as
        type-equivalent types were used.  But it's also allowed for the
        derived ctd to use the element name constraining it to a derivation of
        the element base type.  (Go see namespace
        http://www.opengis.net/ows/1.1 types PositionType, PositionType2D,
        BoundingBox, and WGS84BoundingBox for an example).  So, we really do
        have to have the element's type resolved.

        Except that if a CTD's content incorporates an element with the same
        type as the CTD (i.e., nested), this will never happen, because the
        CTD can't get resolved until after it has been resolved.
        (Go see {http://www.opengis.net/ows/1.1}ContentsBaseType and
        {http://www.opengis.net/ows/1.1}DatasetDescriptionSummaryBaseType for
        an example).

        So, we give the world a break and assume that if the type we're trying
        to resolve is the same as the type of an element in that type, then
        the element type will be resolved by the point it's needed.  In point
        of fact, it won't, but we'll only notice that if a CTD contains an
        element whose type is a restriction of the CTD.  In that case,
        isDerivationConsistent will blow chunks and somebody'll have to come
        back and finish up this mess.
        """

        if not self.isResolved():
            return False
        if self.typeDefinition().isResolved():
            return True
        # Aw, dammit.  See if we're gonna need the type resolved before we can
        # adapt this thing.
        existing_decl = ctd.lookupScopedElementDeclaration(self.expandedName())
        if existing_decl is None:
            # Nobody else has this name, so we don't have to check for
            # consistency.
            return True
        # OK, we've got a name clash.  Are the two types trivially equivalent?
        if self.typeDefinition().isTypeEquivalent(existing_decl.typeDefinition()):
            # Yes! Go for it.
            return True
        # No.  Can't proceed until the type definition is resolved.  Hope it
        # can be....
        _log.warning('Require %s to be resolved; might be a loop.', self.typeDefinition())
        return False

    # aFS:ED
    def _adaptForScope (self, owner, ctd):
        rv = self
        assert isinstance(ctd, ComplexTypeDefinition), '%s is not a CTD' % (ctd,)
        if not isinstance(self.scope(), ComplexTypeDefinition):
            assert owner is not None
            rv = self._clone(owner, ctd._objectOrigin())
            rv._setScope(ctd)
        ctd._recordLocalDeclaration(rv)
        return rv

    __isResolved = False
    def isResolved (self):
        return self.__isResolved

    # res:ED res:ElementDeclaration
    def _resolve (self):
        if self.isResolved():
            return self

        #if self._scopeIsIndeterminate():
        #   _log.debug('WARNING: Resolving ED %s with indeterminate scope (is this a problem?)', self.expandedName())
        if self.__substitutionGroupExpandedName is not None:
            sga = self.__substitutionGroupExpandedName.elementDeclaration()
            if sga is None:
                raise pyxb.SchemaValidationError('Element declaration refers to unrecognized substitution group %s' % (self.__substitutionGroupExpandedName,))
            self.__substitutionGroupAffiliation = sga

        if self.__typeDefinition is None:
            assert self.__typeExpandedName is not None
            td = self.__typeExpandedName.typeDefinition()
            if td is None:
                raise pyxb.SchemaValidationError('Type declaration %s cannot be found' % (self.__typeExpandedName,))
            self._typeDefinition(td)
        self.__isResolved = True
        return self

    def _walkParticleTree (self, visit, arg):
        visit(self, None, arg)

    def __str__ (self):
        if self.typeDefinition() is not None:
            return 'ED[%s:%s]' % (self.name(), self.typeDefinition().name())
        return 'ED[%s:?]' % (self.name(),)


class ComplexTypeDefinition (_SchemaComponent_mixin, _NamedComponent_mixin, pyxb.namespace.resolution._Resolvable_mixin, _Annotated_mixin, _AttributeWildcard_mixin):
    __PrivateTransient = set()

    # The type resolved from the base attribute.
    __baseTypeDefinition = None
    def baseTypeDefinition (self):
        """The type resolved from the base attribute."""
        return self.__baseTypeDefinition

    DM_empty = 0                #<<< No derivation method specified
    DM_extension = 0x01         #<<< Derivation by extension
    DM_restriction = 0x02       #<<< Derivation by restriction

    _DM_Map = { 'extension' : DM_extension
              , 'restriction' : DM_restriction }

    # How the type was derived (a DM_* value)
    # (This field is used to identify unresolved definitions.)
    __derivationMethod = None
    def derivationMethod (self):
        """How the type was derived."""
        return self.__derivationMethod

    # Derived from the final and finalDefault attributes
    __final = DM_empty

    # Derived from the abstract attribute
    __abstract = False
    def abstract (self):
        return self.__abstract

    # A frozenset() of AttributeUse instances.
    __attributeUses = None
    def attributeUses (self):
        """A frozenset() of AttributeUse instances."""
        return self.__attributeUses

    # A map from NCNames to AttributeDeclaration instances that are
    # local to this type.
    __scopedAttributeDeclarations = None
    def lookupScopedAttributeDeclaration (self, expanded_name):
        """Find an attribute declaration with the given name that is local to this type.

        Returns None if there is no such local attribute declaration."""
        if self.__scopedAttributeDeclarations is None:
            return None
        return self.__scopedAttributeDeclarations.get(expanded_name)

    # A map from NCNames to ElementDeclaration instances that are
    # local to this type.
    __scopedElementDeclarations = None
    def lookupScopedElementDeclaration (self, expanded_name):
        """Find an element declaration with the given name that is local to this type.

        Returns None if there is no such local element declaration."""
        if self.__scopedElementDeclarations is None:
            return None
        return self.__scopedElementDeclarations.get(expanded_name)

    __localScopedDeclarations = None
    def localScopedDeclarations (self, reset=False):
        """Return a list of element and attribute declarations that were
        introduced in this definition (i.e., their scope is this CTD).

        @note: This specifically returns a list, with element declarations
        first, because name binding should privilege the elements over the
        attributes.  Within elements and attributes, the components are sorted
        by expanded name, to ensure consistency across a series of binding
        generations.

        @keyword reset: If C{False} (default), a cached previous value (if it
        exists) will be returned.
        """
        if reset or (self.__localScopedDeclarations is None):
            rve = [ _ed for _ed in six.itervalues(self.__scopedElementDeclarations) if (self == _ed.scope()) ]
            rve.sort(key=lambda _x: _x.expandedName())
            rva = [ _ad for _ad in six.itervalues(self.__scopedAttributeDeclarations) if (self == _ad.scope()) ]
            rva.sort(key=lambda _x: _x.expandedName())
            self.__localScopedDeclarations = rve
            self.__localScopedDeclarations.extend(rva)
        return self.__localScopedDeclarations

    def _recordLocalDeclaration (self, decl):
        """Record the given declaration as being locally scoped in
        this type."""
        assert isinstance(decl, _ScopedDeclaration_mixin)
        if isinstance(decl, ElementDeclaration):
            scope_map = self.__scopedElementDeclarations
        elif isinstance(decl, AttributeDeclaration):
            scope_map = self.__scopedAttributeDeclarations
        else:
            raise pyxb.LogicError('Unexpected instance of %s recording as local declaration' % (type(decl),))
        decl_en = decl.expandedName()
        existing_decl = scope_map.setdefault(decl_en, decl)
        if decl != existing_decl:
            if isinstance(decl, ElementDeclaration):
                # Test cos-element-consistent
                existing_type = existing_decl.typeDefinition()
                pending_type = decl.typeDefinition()
                if not pending_type.isDerivationConsistent(existing_type):
                    raise pyxb.SchemaValidationError('Conflicting element declarations for %s: existing %s versus new %s' % (decl.expandedName(), existing_type, pending_type))
            elif isinstance(decl, AttributeDeclaration):
                raise pyxb.SchemaValidationError('Multiple attribute declarations for %s' % (decl.expandedName(),))
            else:
                assert False, 'Unrecognized type %s' % (type(decl),)
        decl._baseDeclaration(existing_decl)
        return self

    def _isHierarchyRoot (self):
        """Return C{True} iff this is the root of a complex type definition hierarchy.
        """
        base = self.__baseTypeDefinition
        return isinstance(base, SimpleTypeDefinition) or base.isUrTypeDefinition()

    CT_EMPTY = 'EMPTY'                 #<<< No content
    CT_SIMPLE = 'SIMPLE'               #<<< Simple (character) content
    CT_MIXED = 'MIXED'                 #<<< Children may be elements or other (e.g., character) content
    CT_ELEMENT_ONLY = 'ELEMENT_ONLY'   #<<< Expect only element content.

    def _contentTypeTag (self):
        """Return the value of the content type identifier, i.e. one of the
        CT_ constants.  Return value is None if no content type has been
        defined."""
        if isinstance(self.__contentType, tuple):
            return self.__contentType[0]
        return self.__contentType

    def _contentTypeComponent (self):
        if isinstance(self.__contentType, tuple):
            return self.__contentType[1]
        return None

    # Identify the sort of content in this type.
    __contentType = None
    def contentType (self):
        """Identify the sort of content in this type.

        Valid values are:
         - C{CT_EMPTY}
         - ( C{CT_SIMPLE}, a L{SimpleTypeDefinition} instance )
         - ( C{CT_MIXED}, a L{Particle} instance )
         - ( C{CT_ELEMENT_ONLY}, a L{Particle} instance )
        """
        return self.__contentType

    def contentTypeAsString (self):
        if self.CT_EMPTY == self.contentType():
            return 'EMPTY'
        ( tag, particle ) = self.contentType()
        if self.CT_SIMPLE == tag:
            return 'Simple [%s]' % (particle,)
        if self.CT_MIXED == tag:
            return 'Mixed [%s]' % (particle,)
        if self.CT_ELEMENT_ONLY == tag:
            return 'Element [%s]' % (particle,)
        raise pyxb.LogicError('Unhandled content type')

    # Derived from the block and blockDefault attributes
    __prohibitedSubstitutions = DM_empty

    # @todo: Extracted from children of various types
    __annotations = None

    def __init__ (self, *args, **kw):
        super(ComplexTypeDefinition, self).__init__(*args, **kw)
        self.__derivationMethod = kw.get('derivation_method')
        self.__scopedElementDeclarations = { }
        self.__scopedAttributeDeclarations = { }

    def hasWildcardElement (self):
        """Return True iff this type includes a wildcard element in
        its content model."""
        if self.CT_EMPTY == self.contentType():
            return False
        ( tag, particle ) = self.contentType()
        if self.CT_SIMPLE == tag:
            return False
        return particle.hasWildcardElement()

    def _updateFromOther_csc (self, other):
        """Override fields in this instance with those from the other.

        This method is invoked only by Schema._addNamedComponent, and
        then only when a built-in type collides with a schema-defined
        type.  Material like facets is not (currently) held in the
        built-in copy, so the DOM information is copied over to the
        built-in STD, which is subsequently re-resolved.

        Returns self.
        """
        assert self != other
        assert self.isNameEquivalent(other)
        super(ComplexTypeDefinition, self)._updateFromOther_csc(other)

        if not other.isResolved():
            if pyxb.namespace.BuiltInObjectUID != self._objectOrigin().generationUID():
                self.__derivationMethod = None

        return self

    __UrTypeDefinition = None
    @classmethod
    def UrTypeDefinition (cls, schema=None, in_builtin_definition=False):
        """Create the ComplexTypeDefinition instance that approximates
        the ur-type.

        See section 3.4.7.
        """

        # The first time, and only the first time, this is called, a
        # namespace should be provided which is the XMLSchema
        # namespace for this run of the system.  Please, do not try to
        # allow this by clearing the type definition.
        #if in_builtin_definition and (cls.__UrTypeDefinition is not None):
        #    raise pyxb.LogicError('Multiple definitions of UrType')
        if cls.__UrTypeDefinition is None:
            # NOTE: We use a singleton subclass of this class
            assert schema is not None

            ns_ctx = schema.targetNamespace().initialNamespaceContext()

            kw = { 'name' : 'anyType',
                   'schema' : schema,
                   'namespace_context' : ns_ctx,
                   'binding_namespace' : schema.targetNamespace(),
                   'derivation_method' : cls.DM_restriction,
                   'scope' : _ScopedDeclaration_mixin.SCOPE_global }
            bi = _UrTypeDefinition(**kw)

            # The ur-type is its own baseTypeDefinition
            bi.__baseTypeDefinition = bi

            # No constraints on attributes
            bi._setAttributeWildcard(Wildcard(namespace_constraint=Wildcard.NC_any, process_contents=Wildcard.PC_lax, **kw))

            # There isn't anything to look up, but context is still global.
            # No declarations will be created, so use indeterminate scope to
            # be consistent with validity checks in Particle constructor.
            # Content is mixed, with elements completely unconstrained. @todo:
            # not associated with a schema (it should be)
            kw = { 'namespace_context' : ns_ctx
                 , 'schema' : schema
                 , 'scope': _ScopedDeclaration_mixin.XSCOPE_indeterminate }
            w = Wildcard(namespace_constraint=Wildcard.NC_any, process_contents=Wildcard.PC_lax, **kw)
            p = Particle(w, min_occurs=0, max_occurs=None, **kw)
            m = ModelGroup(compositor=ModelGroup.C_SEQUENCE, particles=[ p ], **kw)
            bi.__contentType = ( cls.CT_MIXED, Particle(m, **kw) )

            # No attribute uses
            bi.__attributeUses = set()

            # No constraints on extension or substitution
            bi.__final = cls.DM_empty
            bi.__prohibitedSubstitutions = cls.DM_empty

            bi.__abstract = False

            # Refer to it by name
            bi.setNameInBinding(bi.name())

            # The ur-type is always resolved
            bi.__derivationMethod = cls.DM_restriction

            cls.__UrTypeDefinition = bi
        return cls.__UrTypeDefinition

    def isBuiltin (self):
        """Indicate whether this simple type is a built-in type."""
        return (self.UrTypeDefinition() == self)

    # bR:CTD
    def _bindingRequires_vx (self, include_lax):
        """Complex type definitions depend on their base type definition, the
        type definitions of any local attribute declarations, and if strict
        the type definitions of any local element declarations."""
        rv = set()
        assert self.__baseTypeDefinition is not None
        rv.add(self.__baseTypeDefinition)
        for decl in self.localScopedDeclarations():
            if include_lax or isinstance(decl, AttributeDeclaration):
                rv.add(decl.typeDefinition())
        if include_lax:
            ct = self._contentTypeComponent()
            if ct is not None:
                rv.add(ct)
        return frozenset(rv)

    # CFD:CTD CFD:ComplexTypeDefinition
    @classmethod
    def CreateFromDOM (cls, node, **kw):
        # Node should be an XMLSchema complexType node
        assert xsd.nodeIsNamed(node, 'complexType')

        name = domutils.NodeAttribute(node, 'name')

        rv = cls(name=name, node=node, derivation_method=None, **kw)

        # Most of the time, the scope will be global.  It can be something
        # else only if this is an anonymous CTD (created within an element
        # declaration which itself may be global, in a containing CTD, or in a
        # model group).
        if rv._scopeIsGlobal():
            assert isinstance(rv.owner(), Schema)
            if rv.isAnonymous():
                raise pyxb.SchemaValidationError("Anonymous complex type at schema top level")
        else:
            assert not isinstance(rv.owner(), Schema)
            if not rv.isAnonymous():
                raise pyxb.SchemaValidationError('Name attribute invalid on non-global complex types: %s' % (rv.expandedName(),))

        kw.pop('node', None)
        kw['owner'] = rv
        kw['scope'] = rv

        return rv.__setContentFromDOM(node, **kw)

    __baseExpandedName = None

    __ckw = None
    __anyAttribute = None
    __attributeGroupNames = None
    __usesC1 = None
    __usesC1C2 = None
    __attributeGroups = None
    __PrivateTransient.update(['ckw', 'anyAttribute', 'attributeGroupNames', 'usesC1', 'usesC1C2', 'attributeGroups' ])

    # Handle attributeUses, attributeWildcard, contentType
    def __completeProcessing (self, method, content_style):

        if self.__usesC1C2 is None:
            # Handle clauses 1 and 2 (common between simple and complex types)
            uses_c1 = self.__usesC1 # attribute children
            uses_c2 = set()  # attribute group children
            self.__attributeGroups = []
            for ag_en in self.__attributeGroupNames:
                agd = ag_en.attributeGroupDefinition()
                if agd is None:
                    raise pyxb.SchemaValidationError('Attribute group %s cannot be found' % (ag_en,))
                if not agd.isResolved():
                    self._queueForResolution('unresolved attribute group', depends_on=agd)
                    return self
                self.__attributeGroups.append(agd)
                uses_c2.update(agd.attributeUses())

            uses_c1c2 = uses_c1.union(uses_c2)
            for au in uses_c1c2:
                if not au.isResolved():
                    self._queueForResolution('attribute use not resolved')
                    return self
                ad = au.attributeDeclaration()
                if not ad.isResolved():
                    ad_en = ad.expandedName()
                    self._queueForResolution('unresolved attribute declaration %s from base type' % (ad_en,), depends_on=ad)
                    return self

            self.__usesC1C2 = frozenset([ _u._adaptForScope(self) for _u in uses_c1c2 ])

        # Handle clause 3.  Note the slight difference in description between
        # simple and complex content is just that the complex content doesn't
        # bother to check that the base type definition is a complex type
        # definition.  So the same code should work for both, and we don't
        # bother to check content_style.
        uses_c3 = set()  # base attributes
        if isinstance(self.__baseTypeDefinition, ComplexTypeDefinition):
            # NB: The base type definition should be resolved, which means
            # that all its attribute uses have been adapted for scope already
            uses_c3 = set(self.__baseTypeDefinition.__attributeUses)
            assert self.__baseTypeDefinition.isResolved()
            for au in uses_c3:
                if not au.isResolved():
                    self._queueForResolution('unresolved attribute use from base type', depends_on=au)
                    return self
                ad = au.attributeDeclaration()
                if not ad.isResolved():
                    ad_en = ad.expandedName()
                    self._queueForResolution('unresolved attribute declaration %s from base type' % (ad_en,), depends_on=ad)
                    return self
                assert not au.attributeDeclaration()._scopeIsIndeterminate()

            if self.DM_restriction == method:
                # Exclude attributes per clause 3.  Note that this process
                # handles both 3.1 and 3.2, since we have not yet filtered
                # uses_c1 for prohibited attributes.
                for au in self.__usesC1C2:
                    matching_uses = au.matchingQNameMembers(uses_c3)
                    assert matching_uses is not None
                    assert 1 >= len(matching_uses), 'Multiple inherited attribute uses with name %s'
                    for au2 in matching_uses:
                        assert au2.isResolved()
                        uses_c3.remove(au2)
                        au._setRestrictionOf(au2)
            else:
                # In theory, the same attribute name can't appear in the base
                # and sub types because that would violate the local
                # declaration constraint.
                assert self.DM_extension == method

        use_map = { }
        for au in self.__usesC1C2.union(uses_c3):
            assert au.isResolved()
            ad_en = au.attributeDeclaration().expandedName()
            if ad_en in use_map:
                raise pyxb.SchemaValidationError('Multiple definitions for %s in CTD %s' % (ad_en, self.expandedName()))
            use_map[ad_en] = au

        # Past the last point where we might not resolve this instance.  Store
        # the attribute uses, also recording local attribute declarations.
        self.__attributeUses = frozenset(six.itervalues(use_map))
        if not self._scopeIsIndeterminate():
            for au in self.__attributeUses:
                assert not au.attributeDeclaration()._scopeIsIndeterminate(), 'indeterminate scope for %s' % (au,)

        # @todo: Handle attributeWildcard
        # Clause 1
        local_wildcard = None
        if self.__anyAttribute is not None:
            local_wildcard = Wildcard.CreateFromDOM(self.__anyAttribute)

        # Clause 2
        complete_wildcard = _AttributeWildcard_mixin.CompleteWildcard(self._namespaceContext(), self.__attributeGroups, local_wildcard)

        # Clause 3
        if self.DM_restriction == method:
            # Clause 3.1
            self._setAttributeWildcard(complete_wildcard)
        else:
            assert (self.DM_extension == method)
            assert self.baseTypeDefinition().isResolved()
            # 3.2.1
            base_wildcard = None
            if isinstance(self.baseTypeDefinition(), ComplexTypeDefinition):
                base_wildcard = self.baseTypeDefinition().attributeWildcard()
            # 3.2.2
            if base_wildcard is not None:
                if complete_wildcard is None:
                    # 3.2.2.1.1
                    self._setAttributeWildcard(base_wildcard)
                else:
                    # 3.2.2.1.2
                    self._setAttributeWildcard(Wildcard (process_contents=complete_wildcard.processContents(),
                                                         namespace_constraint = Wildcard.IntensionalUnion([complete_wildcard.namespaceConstraint(),
                                                                                                 base_wildcard.namespaceConstraint()]),
                                                         annotation=complete_wildcard.annotation(),
                                                         namespace_context=self._namespaceContext()))
            else:
                # 3.2.2.2
                self._setAttributeWildcard(complete_wildcard)

        # @todo: Make sure we didn't miss any child nodes

        # Remove local attributes we will never use again
        del self.__usesC1
        del self.__usesC1C2
        del self.__attributeGroups
        self.__ckw = None

        # Only now that we've succeeded do we store the method, which
        # marks this component resolved.

        self.__derivationMethod = method
        return self

    def __simpleContent (self, method, **kw):
        # Do content type
        if isinstance(self.__baseTypeDefinition, ComplexTypeDefinition):
            # Clauses 1, 2, and 3 might apply
            parent_content_type = self.__baseTypeDefinition.__contentType
            if ((type(parent_content_type) == tuple) \
                    and (self.CT_SIMPLE == parent_content_type[0]) \
                    and (self.DM_restriction == method)):
                # Clause 1
                assert self.__ctscRestrictionNode is not None
                std = self.__ctscClause2STD
                if std is None:
                    std = parent_content_type[1]
                assert isinstance(std, SimpleTypeDefinition)
                if not std.isResolved():
                    return None
                restriction_node = self.__ctscRestrictionNode
                self.__ctscClause2STD = None
                self.__ctscRestrictionNode = None
                return ( self.CT_SIMPLE, std._createRestriction(self, restriction_node) )
            if ((type(parent_content_type) == tuple) \
                    and (self.CT_MIXED == parent_content_type[0]) \
                    and parent_content_type[1].isEmptiable()):
                # Clause 2
                assert isinstance(self.__ctscClause2STD, SimpleTypeDefinition)
                return ( self.CT_SIMPLE, self.__ctscClause2STD )
            # Clause 3
            return parent_content_type
        # Clause 4
        return ( self.CT_SIMPLE, self.__baseTypeDefinition )

    __ctscClause2STD = None
    __ctscRestrictionNode = None
    __PrivateTransient.update(['ctscRestrictionNode' ])
    __effectiveMixed = None
    __effectiveContent = None
    __pendingDerivationMethod = None
    __isComplexContent = None
    def _isComplexContent (self):
        return self.__isComplexContent
    __ctscRestrictionMode = None
    __contentStyle = None

    def __setComplexContentFromDOM (self, type_node, content_node, definition_node_list, method, **kw):
        # Do content type.  Cache the keywords that need to be used
        # for newly created schema components.
        ckw = kw.copy()
        ckw['namespace_context'] = pyxb.namespace.NamespaceContext.GetNodeContext(type_node)

        # Definition 1: effective mixed
        mixed_attr = None
        if content_node is not None:
            mixed_attr = domutils.NodeAttribute(content_node, 'mixed')
        if mixed_attr is None:
            mixed_attr = domutils.NodeAttribute(type_node, 'mixed')
        if mixed_attr is not None:
            effective_mixed = datatypes.boolean(mixed_attr)
        else:
            effective_mixed = False

        # Definition 2: effective content
        test_2_1_1 = True
        test_2_1_2 = False
        test_2_1_3 = False
        typedef_node = None
        for cn in definition_node_list:
            if Node.ELEMENT_NODE != cn.nodeType:
                continue
            if xsd.nodeIsNamed(cn, 'simpleContent', 'complexContent'):
                # Should have found the content node earlier.
                raise pyxb.LogicError('Missed explicit wrapper in complexType content')
            if Particle.IsTypedefNode(cn):
                typedef_node = cn
                test_2_1_1 = False
            if xsd.nodeIsNamed(cn, 'all', 'sequence') \
                    and (not domutils.HasNonAnnotationChild(cn)):
                test_2_1_2 = True
            if xsd.nodeIsNamed(cn, 'choice') \
                    and (not domutils.HasNonAnnotationChild(cn)):
                mo_attr = domutils.NodeAttribute(cn, 'minOccurs')
                if ((mo_attr is not None) \
                        and (0 == datatypes.integer(mo_attr))):
                    test_2_1_3 = True
        satisfied_predicates = 0
        if test_2_1_1:
            satisfied_predicates += 1
        if test_2_1_2:
            satisfied_predicates += 1
        if test_2_1_3:
            satisfied_predicates += 1
        if 1 == satisfied_predicates:
            if effective_mixed:
                # Clause 2.1.4
                assert (typedef_node is None) or test_2_1_2
                m = ModelGroup(compositor=ModelGroup.C_SEQUENCE, particles=[], **ckw)
                effective_content = Particle(m, **ckw)
            else:
                # Clause 2.1.5
                effective_content = self.CT_EMPTY
        else:
            # Clause 2.2
            assert typedef_node is not None
            effective_content = Particle.CreateFromDOM(typedef_node, **kw)

        # For issues related to soapenc:Array and the fact that PyXB
        # determines the content of types derived from it is empty, see
        # http://tech.groups.yahoo.com/group/soapbuilders/message/5879 and
        # lament the fact that the WSDL spec is not compatible with XSD.  It
        # is *not* an error in PyXB.

        self.__effectiveMixed = effective_mixed
        self.__effectiveContent = effective_content
        self.__ckw = ckw

    def __complexContent (self, method):
        ckw = self.__ckw

        # Shared from clause 3.1.2
        if self.__effectiveMixed:
            ct = self.CT_MIXED
        else:
            ct = self.CT_ELEMENT_ONLY
        # Clause 3
        if self.DM_restriction == method:
            # Clause 3.1
            if self.CT_EMPTY == self.__effectiveContent:
                # Clause 3.1.1
                content_type = self.CT_EMPTY                     # ASSIGN CT_EMPTY
            else:
                # Clause 3.1.2(.2)
                content_type = ( ct, self.__effectiveContent )         # ASSIGN RESTRICTION
                assert 0 == len(self.__scopedElementDeclarations)
                # Reference the parent element declarations; normally this
                # would happen naturally as a consequence of appending this
                # type's content model to the parent's, but with restriction
                # there is no such re-use unless we do this.
                self.__scopedElementDeclarations.update(self.__baseTypeDefinition.__scopedElementDeclarations)
        else:
            # Clause 3.2
            assert self.DM_extension == method
            assert self.__baseTypeDefinition.isResolved()
            parent_content_type = self.__baseTypeDefinition.contentType()
            if self.CT_EMPTY == self.__effectiveContent:
                content_type = parent_content_type               # ASSIGN EXTENSION PARENT ONLY
            elif self.CT_EMPTY == parent_content_type:
                # Clause 3.2.2
                content_type = ( ct, self.__effectiveContent )         # ASSIGN EXTENSION LOCAL ONLY
            else:
                assert type(parent_content_type) == tuple
                m = ModelGroup(compositor=ModelGroup.C_SEQUENCE, particles=[ parent_content_type[1], self.__effectiveContent ], **ckw)
                content_type = ( ct, Particle(m, **ckw) )        # ASSIGN EXTENSION PARENT AND LOCAL

        assert (self.CT_EMPTY == content_type) or ((type(content_type) == tuple) and (content_type[1] is not None))
        return content_type

    def isResolved (self):
        """Indicate whether this complex type is fully defined.

        All built-in type definitions are resolved upon creation.
        Schema-defined type definitionss are held unresolved until the
        schema has been completely read, so that references to later
        schema-defined types can be resolved.  Resolution is performed
        after the entire schema has been scanned and type-definition
        instances created for all topLevel{Simple,Complex}Types.

        If a built-in type definition is also defined in a schema
        (which it should be), the built-in definition is kept, with
        the schema-related information copied over from the matching
        schema-defined type definition.  The former then replaces the
        latter in the list of type definitions to be resolved.  See
        Schema._addNamedComponent.
        """
        # Only unresolved nodes have an unset derivationMethod
        return (self.__derivationMethod is not None)

    # Back door to allow the ur-type to re-resolve itself.  Only needed when
    # we're generating bindings for XMLSchema itself.
    def _setDerivationMethod (self, derivation_method):
        self.__derivationMethod = derivation_method
        return self

    def __setContentFromDOM (self, node, **kw):
        schema = kw.get('schema')
        assert schema is not None
        self.__prohibitedSubstitutions = schema.blockForNode(node, self._DM_Map)
        self.__final = schema.finalForNode(node, self._DM_Map)

        attr_val = domutils.NodeAttribute(node, 'abstract')
        if attr_val is not None:
            self.__abstract = datatypes.boolean(attr_val)

        # Assume we're in the short-hand case: the entire content is
        # implicitly wrapped in a complex restriction of the ur-type.
        definition_node_list = node.childNodes
        is_complex_content = True
        self.__baseTypeDefinition = ComplexTypeDefinition.UrTypeDefinition()
        method = self.DM_restriction

        # Determine whether above assumption is correct by looking for
        # element content and seeing if it's one of the wrapper
        # elements.
        first_elt = domutils.LocateFirstChildElement(node)
        content_node = None
        clause2_std = None
        ctsc_restriction_node = None
        if first_elt:
            have_content = False
            if xsd.nodeIsNamed(first_elt, 'simpleContent'):
                have_content = True
                is_complex_content = False
            elif xsd.nodeIsNamed(first_elt, 'complexContent'):
                have_content = True
            else:
                # Not one of the wrappers; use implicit wrapper around
                # the children
                if not Particle.IsParticleNode(first_elt, 'attributeGroup', 'attribute', 'anyAttribute'):
                    raise pyxb.SchemaValidationError('Unexpected element %s at root of complexType' % (first_elt.nodeName,))
            if have_content:
                # Repeat the search to verify that only the one child is present.
                content_node = domutils.LocateFirstChildElement(node, require_unique=True)
                assert content_node == first_elt

                # Identify the contained restriction or extension
                # element, and extract the base type.
                ions = domutils.LocateFirstChildElement(content_node, absent_ok=False)
                if xsd.nodeIsNamed(ions, 'restriction'):
                    method = self.DM_restriction
                    if not is_complex_content:
                        # Clause 2 of complex type with simple content
                        ctsc_restriction_node = ions
                        ions_st = domutils.LocateUniqueChild(ions,'simpleType')
                        if ions_st is not None:
                            clause2_std = SimpleTypeDefinition.CreateFromDOM(ions_st, **kw)
                elif xsd.nodeIsNamed(ions, 'extension'):
                    method = self.DM_extension
                else:
                    raise pyxb.SchemaValidationError('Expected restriction or extension as sole child of %s in %s' % (content_node.nodeName, self.name()))
                self.__baseExpandedName = domutils.NodeAttributeQName(ions, 'base')
                if self.__baseExpandedName is None:
                    raise pyxb.SchemaValidationError('Element %s missing base attribute' % (ions.nodeName,))
                self.__baseTypeDefinition = None
                # The content is defined by the restriction/extension element
                definition_node_list = ions.childNodes
        # deriviationMethod is assigned after resolution completes
        self.__pendingDerivationMethod = method
        self.__isComplexContent = is_complex_content
        self.__ctscRestrictionNode = ctsc_restriction_node
        self.__ctscClause2STD = clause2_std

        (attributes, attribute_group_names, any_attribute) = self._attributeRelevantChildren(definition_node_list)
        self.__usesC1 = set()
        for cn in attributes:
            au = AttributeUse.CreateFromDOM(cn, **kw)
            self.__usesC1.add(au)
        self.__attributeGroupNames = attribute_group_names
        self.__anyAttribute = any_attribute

        if self.__isComplexContent:
            self.__setComplexContentFromDOM(node, content_node, definition_node_list, self.__pendingDerivationMethod, **kw)

        # Creation does not attempt to do resolution.  Queue up the newly created
        # whatsis so we can resolve it after everything's been read in.
        self._annotationFromDOM(node)

        if not self.isResolved():
            self._queueForResolution('creation')

        return self

    # Resolution of a CTD can be delayed for the following reasons:
    #
    # * It extends or restricts a base type that has not been resolved
    #   [_resolve]
    #
    # * It refers to an attribute or attribute group that has not been
    #   resolved [__completeProcessing]
    #
    # * It includes an attribute that matches in NCName and namespace
    #   an unresolved attribute from the base type
    #   [__completeProcessing]
    #
    # * The content model includes a particle which cannot be resolved
    #   (so has not contributed any local element declarations).
    # res:CTD
    def _resolve (self):
        if self.isResolved():
            return self

        # @todo: implement prohibitedSubstitutions, final, annotations

        # See whether we've resolved through to the base type
        if self.__baseTypeDefinition is None:
            base_type = self.__baseExpandedName.typeDefinition()
            if base_type is None:
                raise pyxb.SchemaValidationError('Cannot locate %s: need import?' % (self.__baseExpandedName,))
            if not base_type.isResolved():
                # Have to delay resolution until the type this
                # depends on is available.
                self._queueForResolution('unresolved base type %s' % (self.__baseExpandedName,), depends_on=base_type)
                return self
            self.__baseTypeDefinition = base_type

        # Only build the content once.  This will not complete if the content
        # is a restriction of an unresolved simple type; otherwise, it only
        # depends on the base type which we know is good.
        if self.__contentType is None:
            if self.__isComplexContent:
                content_type = self.__complexContent(self.__pendingDerivationMethod)
                self.__contentStyle = 'complex'
            else:
                # The definition node list is not relevant to simple content
                content_type = self.__simpleContent(self.__pendingDerivationMethod)
                if content_type is None:
                    self._queueForResolution('restriction of unresolved simple type')
                    return self
                self.__contentStyle = 'simple'
            assert content_type is not None
            self.__contentType = content_type

        # Last chance for failure is if we haven't been able to
        # extract all the element declarations that might appear in
        # this complex type.  That technically wouldn't stop this from
        # being resolved, but it does prevent us from using it as a
        # context.
        if isinstance(self.__contentType, tuple) and isinstance(self.__contentType[1], Particle):
            prt = self.__contentType[1]
            if not prt.isAdaptable(self):
                self._queueForResolution('content particle %s is not deep-resolved' % (prt,))
                return self
            self.__contentType = (self.__contentType[0], prt._adaptForScope(self, self))

        return self.__completeProcessing(self.__pendingDerivationMethod, self.__contentStyle)

    def pythonSupport (self):
        """Complex type definitions have no built-in type support."""
        return None

    def __str__ (self):
        if self.isAnonymous():
            return 'CTD{Anonymous}[%x]' % (id(self),)
        return 'CTD[%s]' % (self.expandedName(),)

class _UrTypeDefinition (ComplexTypeDefinition, _Singleton_mixin):
    """Subclass ensures there is only one ur-type."""
    def pythonSupport (self):
        """The ur-type does have a Python class backing it up."""
        return datatypes.anyType

    def _resolve (self):
        # The ur type is always resolved, except when it gets unresolved
        # through being updated from an instance read from the schema.
        return self._setDerivationMethod(self.DM_restriction)


class AttributeGroupDefinition (_SchemaComponent_mixin, _NamedComponent_mixin, pyxb.namespace.resolution._Resolvable_mixin, _Annotated_mixin, _AttributeWildcard_mixin):
    """An XMLSchema U{Attribute Group Definition<http://www.w3.org/TR/xmlschema-1/#cAttribute_Group_Definitions>} component."""
    __PrivateTransient = set()

    # A frozenset of AttributeUse instances
    __attributeUses = None

    def __init__ (self, *args, **kw):
        super(AttributeGroupDefinition, self).__init__(*args, **kw)
        #assert 'scope' in kw
        #assert self._scopeIsIndeterminate()

    def __str__ (self):
        return 'AGD[%s]' % (self.expandedName(),)

    @classmethod
    def CreateBaseInstance (cls, name, schema, attribute_uses):
        """Create an attribute declaration component for a specified namespace."""
        kw = { 'name' : name,
               'schema' : schema,
               'namespace_context' : schema.targetNamespace().initialNamespaceContext(),
               'scope' : _ScopedDeclaration_mixin.SCOPE_global }
        bi = cls(**kw)
        bi.__attributeUses = frozenset(attribute_uses)
        bi.__isResolved = True
        return bi

    __anyAttribute = None
    __attributeGroupNames = None
    __PrivateTransient.update(['anyAttribute', 'attributeGroupNames'])

    # CFD:AGD CFD:AttributeGroupDefinition
    @classmethod
    def CreateFromDOM (cls, node, **kw):
        """Create an attribute group definition from the given DOM node.

        """

        assert xsd.nodeIsNamed(node, 'attributeGroup')
        name = domutils.NodeAttribute(node, 'name')

        # Attribute group definitions can only appear at the top level of the
        # schema, and any definitions in them are scope indeterminate until
        # they're referenced in a complex type.
        kw.update({ 'scope' : _ScopedDeclaration_mixin.XSCOPE_indeterminate })
        rv = cls(name=name, node=node, **kw)

        rv._annotationFromDOM(node)

        # Attribute group definitions must not be references
        if domutils.NodeAttribute(node, 'ref'):
            raise pyxb.SchemaValidationError('Attribute reference at top level')

        kw.pop('node', None)
        kw['owner'] = rv

        (attributes, attribute_group_names, any_attribute) = rv._attributeRelevantChildren(node.childNodes)
        rv.__attributeUses = set()
        for cn in attributes:
            rv.__attributeUses.add(AttributeUse.CreateFromDOM(cn, **kw))
        rv.__attributeGroupNames = attribute_group_names
        rv.__anyAttribute = any_attribute

        # Unconditionally queue for resolution, to avoid repeating the
        # wildcard code.
        rv._queueForResolution('creation')

        return rv

    # Indicates whether we have resolved any references
    __isResolved = False
    def isResolved (self):
        return self.__isResolved

    def _resolve (self):
        if self.__isResolved:
            return self

        uses = self.__attributeUses
        attribute_groups = []
        for ag_en in self.__attributeGroupNames:
            agd = ag_en.attributeGroupDefinition()
            if agd is None:
                raise pyxb.SchemaValidationError('Attribute group %s cannot be found' % (ag_en,))
            if not agd.isResolved():
                self._queueForResolution('attributeGroup %s not resolved' % (ag_en,))
                return self
            attribute_groups.append(agd)
            uses = uses.union(agd.attributeUses())

        self.__attributeUses = frozenset(uses)

        # "Complete wildcard" per CTD
        local_wildcard = None
        if self.__anyAttribute is not None:
            local_wildcard = Wildcard.CreateFromDOM(self.__anyAttribute)
        self._setAttributeWildcard(_AttributeWildcard_mixin.CompleteWildcard(self._namespaceContext(), attribute_groups, local_wildcard))

        self.__isResolved = True
        return self

    # bR:AGD
    def _bindingRequires_vx (self, include_lax):
        """Attribute group declarations require their uses, but only if lax."""
        if not include_lax:
            return frozenset()
        return frozenset(self.attributeUses())

    def attributeUses (self):
        return self.__attributeUses

class ModelGroupDefinition (_SchemaComponent_mixin, _NamedComponent_mixin, _Annotated_mixin):
    """An XMLSchema U{Model Group Definition<http://www.w3.org/TR/xmlschema-1/#cModel_Group_Definitions>} component."""
    # Reference to a _ModelGroup
    __modelGroup = None

    def modelGroup (self):
        """The model group for which this definition provides a name."""
        return self.__modelGroup

    # CFD:MGD CFD:ModelGroupDefinition
    @classmethod
    def CreateFromDOM (cls, node, **kw):
        """Create a Model Group Definition from a DOM element node.

        wxs is a Schema instance within which the model group is being
        defined.

        node is a DOM element.  The name must be 'group', and the node
        must be in the XMLSchema namespace.  The node must have a
        'name' attribute, and must not have a 'ref' attribute.
        """
        assert xsd.nodeIsNamed(node, 'group')

        assert domutils.NodeAttribute(node, 'ref') is None

        name = domutils.NodeAttribute(node, 'name')
        kw['scope'] = _ScopedDeclaration_mixin.XSCOPE_indeterminate
        rv = cls(name=name, node=node, **kw)
        rv._annotationFromDOM(node)

        kw.pop('node', None)
        kw['owner'] = rv

        for cn in node.childNodes:
            if Node.ELEMENT_NODE != cn.nodeType:
                continue
            if ModelGroup.IsGroupMemberNode(cn):
                assert not rv.__modelGroup
                # Model group definitions always occur at the top level of the
                # schema, so the elements declared in them are not bound to a
                # scope until they are referenced in a complex type.
                rv.__modelGroup = ModelGroup.CreateFromDOM(cn, model_group_definition=rv, **kw)
        assert rv.__modelGroup is not None
        return rv

    # bR:MGD
    def _bindingRequires_vx (self, include_lax):
        """Model group definitions depend on the contained model group."""
        if not include_lax:
            return frozenset()
        return frozenset([self.__modelGroup])

    def __str__ (self):
        return 'MGD[%s: %s]' % (self.name(), self.modelGroup())


class ModelGroup (_ParticleTree_mixin, _SchemaComponent_mixin, _Annotated_mixin):
    """An XMLSchema U{Model Group<http://www.w3.org/TR/xmlschema-1/#cModel_Group>} component."""
    C_INVALID = 0
    C_ALL = 0x01
    C_CHOICE = 0x02
    C_SEQUENCE = 0x03

    # One of the C_* values above.  Set at construction time from the
    # keyword parameter "compositor".
    __compositor = C_INVALID
    def compositor (self):
        return self.__compositor

    @classmethod
    def CompositorToString (cls, compositor):
        """Map a compositor value to a string."""
        if cls.C_ALL == compositor:
            return 'all'
        if cls.C_CHOICE == compositor:
            return 'choice'
        if cls.C_SEQUENCE == compositor:
            return 'sequence'
        return 'invalid'

    def compositorToString (self):
        """Return a string representing the compositor value."""
        return self.CompositorToString(self.__compositor)

    # A list of Particle instances.  Set at construction time from
    # the keyword parameter "particles".
    __particles = None
    def particles (self):
        return self.__particles

    def isAdaptable (self, ctd):
        """A model group has an unresolvable particle if any of its
        particles is unresolvable.  Duh."""
        for p in self.particles():
            if not p.isAdaptable(ctd):
                return False
        return True

    def effectiveTotalRange (self, particle):
        """Return the minimum and maximum of the number of elements that can
        appear in a sequence matched by this particle.

        See U{http://www.w3.org/TR/xmlschema-1/#cos-seq-range}
        """
        if self.__compositor in (self.C_ALL, self.C_SEQUENCE):
            sum_minoccurs = 0
            sum_maxoccurs = 0
            for prt in self.__particles:
                (prt_min, prt_max) = prt.effectiveTotalRange()
                sum_minoccurs += prt_min
                if sum_maxoccurs is not None:
                    if prt_max is None:
                        sum_maxoccurs = None
                    else:
                        sum_maxoccurs += prt_max
            prod_maxoccurs = particle.maxOccurs()
            if prod_maxoccurs is not None:
                if sum_maxoccurs is None:
                    prod_maxoccurs = None
                else:
                    prod_maxoccurs *= sum_maxoccurs
            return (sum_minoccurs * particle.minOccurs(), prod_maxoccurs)
        assert self.__compositor == self.C_CHOICE
        if 0 == len(self.__particles):
            min_minoccurs = 0
            max_maxoccurs = 0
        else:
            (min_minoccurs, max_maxoccurs) = self.__particles[0].effectiveTotalRange()
            for prt in self.__particles[1:]:
                (prt_min, prt_max) = prt.effectiveTotalRange()
                if prt_min < min_minoccurs:
                    min_minoccurs = prt_min
                if prt_max is None:
                    max_maxoccurs = None
                elif (max_maxoccurs is not None) and (prt_max > max_maxoccurs):
                    max_maxoccurs = prt_max
        min_minoccurs *= particle.minOccurs()
        if (max_maxoccurs is not None) and (particle.maxOccurs() is not None):
            max_maxoccurs *=  particle.maxOccurs()
        return (min_minoccurs, max_maxoccurs)

    # The ModelGroupDefinition that names this ModelGroup, or None if
    # the ModelGroup is anonymous.  This is set at construction time
    # from the keyword parameter "model_group_definition".
    __modelGroupDefinition = None
    def modelGroupDefinition (self):
        """The ModelGroupDefinition that names this group, or None if it is unnamed."""
        return self.__modelGroupDefinition

    def __init__ (self, compositor, particles, *args, **kw):
        """Create a new model group.

        compositor must be a legal compositor value (one of C_ALL, C_CHOICE, C_SEQUENCE).

        particles must be a list of zero or more Particle instances.

        scope is the _ScopeDeclaration_mixin context into which new
        declarations are recorded.  It can be SCOPE_global, a complex
        type definition, or None if this is (or is within) a named
        model group.

        model_group_definition is an instance of ModelGroupDefinition
        if this is a named model group.  It defaults to None
        indicating a local group.
        """

        super(ModelGroup, self).__init__(*args, **kw)
        assert 'scope' in kw
        self.__compositor = compositor
        self.__particles = particles
        self.__modelGroupDefinition = kw.get('model_group_definition')

    def hasWildcardElement (self):
        """Return True if the model includes a wildcard amongst its particles."""
        for p in self.particles():
            if p.hasWildcardElement():
                return True
        return False

    # bR:MG
    def _bindingRequires_vx (self, include_lax):
        if not include_lax:
            return frozenset()
        return frozenset(self.__particles)

    # CFD:MG CFD:ModelGroup
    @classmethod
    def CreateFromDOM (cls, node, **kw):
        """Create a model group from the given DOM node.

        wxs is a Schema instance within which the model group is being
        defined.

        node is a DOM element.  The name must be one of ( 'all',
        'choice', 'sequence' ), and the node must be in the XMLSchema
        namespace.

        scope is the _ScopeDeclaration_mxin context that is assigned
        to declarations that appear within the model group.  It can be
        None, indicating no scope defined, or a complex type
        definition.
        """

        scope = kw['scope']
        assert _ScopedDeclaration_mixin.ScopeIsIndeterminate(scope) or isinstance(scope, ComplexTypeDefinition)

        if xsd.nodeIsNamed(node, 'all'):
            compositor = cls.C_ALL
        elif xsd.nodeIsNamed(node, 'choice'):
            compositor = cls.C_CHOICE
        else:
            assert xsd.nodeIsNamed(node, 'sequence')
            compositor = cls.C_SEQUENCE
        particles = []
        # Remove the owner from particle constructor arguments: we need to set it later
        kw.pop('owner', None)
        for cn in node.childNodes:
            if Node.ELEMENT_NODE != cn.nodeType:
                continue
            if Particle.IsParticleNode(cn):
                # NB: Ancestor of particle is set in the ModelGroup constructor
                particles.append(Particle.CreateFromDOM(node=cn, **kw))
            elif not xsd.nodeIsNamed(cn, 'annotation'):
                raise pyxb.SchemaValidationError('Unexpected element %s in model group' % (cn.nodeName,))
        rv = cls(compositor, particles, node=node, **kw)
        for p in particles:
            p._setOwner(rv)
        rv._annotationFromDOM(node)
        return rv

    @classmethod
    def IsGroupMemberNode (cls, node):
        return xsd.nodeIsNamed(node, 'all', 'choice', 'sequence')

    # aFS:MG
    def _adaptForScope (self, owner, ctd):
        rv = self
        assert isinstance(ctd, ComplexTypeDefinition)
        maybe_rv = self._clone(owner, ctd._objectOrigin())
        scoped_particles = [ _p._adaptForScope(maybe_rv, ctd) for _p in self.particles() ]
        do_clone = (self._scope() != ctd) or (self.particles() != scoped_particles)
        if do_clone:
            rv = maybe_rv
            rv.__particles = scoped_particles
        return rv

    def _walkParticleTree (self, visit, arg):
        visit(self, True, arg)
        for p in self.particles():
            p._walkParticleTree(visit, arg)
        visit(self, False, arg)

    def __str__ (self):
        comp = None
        if self.C_ALL == self.compositor():
            comp = 'ALL'
        elif self.C_CHOICE == self.compositor():
            comp = 'CHOICE'
        elif self.C_SEQUENCE == self.compositor():
            comp = 'SEQUENCE'
        return '%s:(%s)' % (comp, six.u(',').join( [ six.text_type(_p) for _p in self.particles() ] ) )

class Particle (_ParticleTree_mixin, _SchemaComponent_mixin, pyxb.namespace.resolution._Resolvable_mixin):
    """An XMLSchema U{Particle<http://www.w3.org/TR/xmlschema-1/#cParticle>} component."""

    # The minimum number of times the term may appear.
    __minOccurs = 1
    def minOccurs (self):
        """The minimum number of times the term may appear.

        Defaults to 1."""
        return self.__minOccurs

    # Upper limit on number of times the term may appear.
    __maxOccurs = 1
    def maxOccurs (self):
        """Upper limit on number of times the term may appear.

        If None, the term may appear any number of times; otherwise,
        this is an integral value indicating the maximum number of times
        the term may appear.  The default value is 1; the value, unless
        None, must always be at least minOccurs().
        """
        return self.__maxOccurs

    # A reference to a ModelGroup, WildCard, or ElementDeclaration
    __term = None
    def term (self):
        """A reference to a ModelGroup, Wildcard, or ElementDeclaration."""
        return self.__term
    __pendingTerm = None

    __refExpandedName = None
    __resolvableType = None

    def effectiveTotalRange (self):
        """Extend the concept of effective total range to all particles.

        See U{http://www.w3.org/TR/xmlschema-1/#cos-seq-range} and
        U{http://www.w3.org/TR/xmlschema-1/#cos-choice-range}
        """
        if isinstance(self.__term, ModelGroup):
            return self.__term.effectiveTotalRange(self)
        return (self.minOccurs(), self.maxOccurs())

    def isEmptiable (self):
        """Return C{True} iff this particle can legitimately match an empty
        sequence (no content).

        See U{http://www.w3.org/TR/xmlschema-1/#cos-group-emptiable}
        """
        return 0 == self.effectiveTotalRange()[0]

    def hasWildcardElement (self):
        """Return True iff this particle has a wildcard in its term.

        Note that the wildcard may be in a nested model group."""
        return self.term().hasWildcardElement()

    def __init__ (self, term, *args, **kw):
        """Create a particle from the given DOM node.

        term is a XML Schema Component: one of ModelGroup,
        ElementDeclaration, and Wildcard.

        The following keyword arguments are processed:

        min_occurs is a non-negative integer value with default 1,
        denoting the minimum number of terms required by the content
        model.

        max_occurs is a positive integer value with default 1, or None
        indicating unbounded, denoting the maximum number of terms
        allowed by the content model.

        scope is the _ScopeDeclaration_mxin context that is assigned
        to declarations that appear within the particle.  It can be
        None, indicating no scope defined, or a complex type
        definition.
        """

        super(Particle, self).__init__(*args, **kw)

        min_occurs = kw.get('min_occurs', 1)
        max_occurs = kw.get('max_occurs', 1)

        assert 'scope' in kw
        assert (self._scopeIsIndeterminate()) or isinstance(self._scope(), ComplexTypeDefinition)

        if term is not None:
            self.__term = term

        assert isinstance(min_occurs, six.integer_types)
        self.__minOccurs = min_occurs
        assert (max_occurs is None) or isinstance(max_occurs, six.integer_types)
        self.__maxOccurs = max_occurs
        if self.__maxOccurs is not None:
            if self.__minOccurs > self.__maxOccurs:
                raise pyxb.LogicError('Particle minOccurs %s is greater than maxOccurs %s on creation' % (min_occurs, max_occurs))

    # res:Particle
    def _resolve (self):
        if self.isResolved():
            return self

        # @RESOLUTION@
        if ModelGroup == self.__resolvableType:
            group_decl = self.__refExpandedName.modelGroupDefinition()
            if group_decl is None:
                raise pyxb.SchemaValidationError('Model group reference %s cannot be found' % (self.__refExpandedName,))

            self.__pendingTerm = group_decl.modelGroup()
            assert self.__pendingTerm is not None
        elif ElementDeclaration == self.__resolvableType:
            # 3.9.2 says use 3.3.2, which is Element.  The element inside a
            # particle is a localElement, so we either get the one it refers
            # to (which is top-level), or create a local one here.
            if self.__refExpandedName is not None:
                assert self.__pendingTerm is None
                self.__pendingTerm = self.__refExpandedName.elementDeclaration()
                if self.__pendingTerm is None:
                    raise pyxb.SchemaValidationError('Unable to locate element referenced by %s' % (self.__refExpandedName,))
            assert self.__pendingTerm is not None

            # Whether this is a local declaration or one pulled in from the
            # global type definition symbol space, its name is now reserved in
            # this type.
            assert self.__pendingTerm is not None
        else:
            assert False

        self.__term = self.__pendingTerm
        assert self.__term is not None

        return self

    def isResolved (self):
        return self.__term is not None

    # CFD:Particle
    @classmethod
    def CreateFromDOM (cls, node, **kw):
        """Create a particle from the given DOM node.

        wxs is a Schema instance within which the model group is being
        defined.

        node is a DOM element.  The name must be one of ( 'group',
        'element', 'any', 'all', 'choice', 'sequence' ), and the node
        must be in the XMLSchema namespace.

        scope is the _ScopeDeclaration_mxin context that is assigned
        to declarations that appear within the model group.  It can be
        None, indicating no scope defined, or a complex type
        definition.
        """
        scope = kw['scope']
        assert _ScopedDeclaration_mixin.ScopeIsIndeterminate(scope) or isinstance(scope, ComplexTypeDefinition)

        kw.update({ 'min_occurs' : 1
                  , 'max_occurs' : 1
                  , 'node' : node })

        if not Particle.IsParticleNode(node):
            raise pyxb.LogicError('Attempted to create particle from illegal element %s' % (node.nodeName,))
        attr_val = domutils.NodeAttribute(node, 'minOccurs')
        if attr_val is not None:
            kw['min_occurs'] = datatypes.nonNegativeInteger(attr_val)
        attr_val = domutils.NodeAttribute(node, 'maxOccurs')
        if attr_val is not None:
            if 'unbounded' == attr_val:
                kw['max_occurs'] = None
            else:
                kw['max_occurs'] = datatypes.nonNegativeInteger(attr_val)

        rv = cls(None, **kw)

        kw.pop('node', None)
        kw['owner'] = rv

        rv.__refExpandedName = domutils.NodeAttributeQName(node, 'ref')
        rv.__pendingTerm = None
        rv.__resolvableType = None
        if xsd.nodeIsNamed(node, 'group'):
            # 3.9.2 says use 3.8.2, which is ModelGroup.  The group
            # inside a particle is a groupRef.  If there is no group
            # with that name, this throws an exception as expected.
            if rv.__refExpandedName is None:
                raise pyxb.SchemaValidationError('group particle without reference')
            rv.__resolvableType = ModelGroup
        elif xsd.nodeIsNamed(node, 'element'):
            if rv.__refExpandedName is None:
                schema = kw.get('schema')
                assert schema is not None
                target_namespace = schema.targetNamespaceForNode(node, ElementDeclaration)
                incoming_tns = kw.get('target_namespace')
                if incoming_tns is not None:
                    assert incoming_tns == target_namespace
                else:
                    kw['target_namespace'] = target_namespace
                rv.__term = ElementDeclaration.CreateFromDOM(node=node, **kw)
            else:
                # NOTE: 3.3.3 clause 2.2 specifies that if ref is used, all
                # the other configuration attributes like nillable and default
                # must be absent.
                for tag in ('nillable', 'default', 'fixed', 'form', 'block', 'type'):
                    av = domutils.NodeAttribute(node, tag)
                    if av is not None:
                        raise pyxb.SchemaValidationError('element with "ref" cannot have "%s"' % (tag,))
                rv.__resolvableType = ElementDeclaration
                assert not xsd.nodeIsNamed(node.parentNode, 'schema')
        elif xsd.nodeIsNamed(node, 'any'):
            # 3.9.2 says use 3.10.2, which is Wildcard.
            rv.__term = Wildcard.CreateFromDOM(node=node)
        elif ModelGroup.IsGroupMemberNode(node):
            # Choice, sequence, and all inside a particle are explicit
            # groups (or a restriction of explicit group, in the case
            # of all)
            rv.__term = ModelGroup.CreateFromDOM(node, **kw)
        else:
            raise pyxb.LogicError('Unhandled node in Particle.CreateFromDOM: %s' % (node.toxml("utf-8"),))

        if not rv.isResolved():
            rv._queueForResolution('creation')
        return rv

    # bR:PRT
    def _bindingRequires_vx (self, include_lax):
        if not include_lax:
            return frozenset()
        return frozenset([ self.__term ])

    # aFS:PRT
    def _adaptForScope (self, owner, ctd):
        rv = self
        assert isinstance(ctd, ComplexTypeDefinition)
        maybe_rv = self._clone(owner, ctd._objectOrigin())
        term = rv.__term._adaptForScope(maybe_rv, ctd)
        do_clone = (self._scope() != ctd) or (rv.__term != term)
        if  do_clone:
            rv = maybe_rv
            rv.__term = term
        return rv

    def isAdaptable (self, ctd):
        """A particle has an unresolvable particle if it cannot be
        resolved, or if it has resolved to a term which is a model
        group that has an unresolvable particle.
        """
        if not self.isResolved():
            return False
        return self.term().isAdaptable(ctd)

    def walkParticleTree (self, visit, arg):
        """The entry-point to walk a particle tree defining a content model.

        See L{_ParticleTree_mixin._walkParticleTree}."""
        self._walkParticleTree(visit, arg)

    def _walkParticleTree (self, visit, arg):
        visit(self, True, arg)
        self.__term._walkParticleTree(visit, arg)
        visit(self, False, arg)

    @classmethod
    def IsTypedefNode (cls, node):
        return xsd.nodeIsNamed(node, 'group', 'all', 'choice', 'sequence')

    @classmethod
    def IsParticleNode (cls, node, *others):
        return xsd.nodeIsNamed(node, 'group', 'all', 'choice', 'sequence', 'element', 'any', *others)

    def __str__ (self):
        #return 'PART{%s:%d,%s}' % (self.term(), self.minOccurs(), self.maxOccurs())
        return 'PART{%s:%d,%s}[%x]' % ('TERM', self.minOccurs(), self.maxOccurs(), id(self))


# 3.10.1
class Wildcard (_ParticleTree_mixin, _SchemaComponent_mixin, _Annotated_mixin):
    """An XMLSchema U{Wildcard<http://www.w3.org/TR/xmlschema-1/#cParticle>} component."""

    NC_any = '##any'            #<<< The namespace constraint "##any"
    NC_not = '##other'          #<<< A flag indicating constraint "##other"
    NC_targetNamespace = '##targetNamespace'
    NC_local = '##local'

    __namespaceConstraint = None
    def namespaceConstraint (self):
        """A constraint on the namespace for the wildcard.

        Valid values are:
         - L{Wildcard.NC_any}
         - A tuple ( L{Wildcard.NC_not}, a_namespace )
         - set(of_namespaces)

        Note that namespace are represented by
        L{Namespace<pyxb.namespace.Namespace>} instances, not the URIs that
        actually define a namespace.  Absence of a namespace is represented by
        C{None}, both in the "not" pair and in the set.
        """
        return self.__namespaceConstraint

    @classmethod
    def IntensionalUnion (cls, constraints):
        """http://www.w3.org/TR/xmlschema-1/#cos-aw-union"""
        assert 0 < len(constraints)
        o1 = constraints.pop(0)
        while 0 < len(constraints):
            o2 = constraints.pop(0)
            # 1
            if (o1 == o2):
                continue
            # 2
            if (cls.NC_any == o1) or (cls.NC_any == o2):
                o1 = cls.NC_any
                continue
            # 3
            if isinstance(o1, set) and isinstance(o2, set):
                o1 = o1.union(o2)
                continue
            # 4
            if (isinstance(o1, tuple) and isinstance(o2, tuple)) and (o1[1] != o2[1]):
                o1 = ( cls.NC_not, None )
                continue
            # At this point, one must be a negated namespace and the
            # other a set.  Identify them.
            c_tuple = None
            c_set = None
            if isinstance(o1, tuple):
                assert isinstance(o2, set)
                c_tuple = o1
                c_set = o2
            else:
                assert isinstance(o1, set)
                assert isinstance(o2, tuple)
                c_tuple = o2
                c_set = o1
            negated_ns = c_tuple[1]
            if negated_ns is not None:
                # 5.1
                if (negated_ns in c_set) and (None in c_set):
                    o1 = cls.NC_any
                    continue
                # 5.2
                if negated_ns in c_set:
                    o1 = ( cls.NC_not, None )
                    continue
                # 5.3
                if None in c_set:
                    raise pyxb.SchemaValidationError('Union of wildcard namespace constraints not expressible')
                o1 = c_tuple
                continue
            # 6
            if None in c_set:
                o1 = cls.NC_any
            else:
                o1 = ( cls.NC_not, None )
        return o1

    @classmethod
    def IntensionalIntersection (cls, constraints):
        """http://www.w3.org/TR/xmlschema-1/#cos-aw-intersect"""
        assert 0 < len(constraints)
        o1 = constraints.pop(0)
        while 0 < len(constraints):
            o2 = constraints.pop(0)
            # 1
            if (o1 == o2):
                continue
            # 2
            if (cls.NC_any == o1) or (cls.NC_any == o2):
                if cls.NC_any == o1:
                    o1 = o2
                continue
            # 4
            if isinstance(o1, set) and isinstance(o2, set):
                o1 = o1.intersection(o2)
                continue
            if isinstance(o1, tuple) and isinstance(o2, tuple):
                ns1 = o1[1]
                ns2 = o2[1]
                # 5
                if (ns1 is not None) and (ns2 is not None) and (ns1 != ns2):
                    raise pyxb.SchemaValidationError('Intersection of wildcard namespace constraints not expressible')
                # 6
                assert (ns1 is None) or (ns2 is None)
                if ns1 is None:
                    assert ns2 is not None
                    o1 = ( cls.NC_not, ns2 )
                else:
                    assert ns1 is not None
                    o1 = ( cls.NC_not, ns1 )
                continue
            # 3
            # At this point, one must be a negated namespace and the
            # other a set.  Identify them.
            c_tuple = None
            c_set = None
            if isinstance(o1, tuple):
                assert isinstance(o2, set)
                c_tuple = o1
                c_set = o2
            else:
                assert isinstance(o1, set)
                assert isinstance(o2, tuple)
                c_tuple = o2
                c_set = o1
            negated_ns = c_tuple[1]
            if negated_ns in c_set:
                c_set.remove(negated_ns)
            if None in c_set:
                c_set.remove(None)
            o1 = c_set
        return o1

    PC_skip = 'skip'            #<<< No constraint is applied
    PC_lax = 'lax'              #<<< Validate against available uniquely determined declaration
    PC_strict = 'strict'        #<<< Validate against declaration or xsi:type which must be available

    # One of PC_*
    __processContents = None
    def processContents (self):
        return self.__processContents

    def hasWildcardElement (self):
        """Return True, since Wildcard components are wildcards."""
        return True

    def __init__ (self, *args, **kw):
        assert 0 == len(args)
        super(Wildcard, self).__init__(*args, **kw)
        self.__namespaceConstraint = kw['namespace_constraint']
        self.__processContents = kw['process_contents']

    def isAdaptable (self, ctd):
        return True

    def _walkParticleTree (self, visit, arg):
        visit(self, None, arg)

    # aFS:WC
    def _adaptForScope (self, owner, ctd):
        """Wildcards are scope-independent; return self"""
        return self

    # CFD:Wildcard
    @classmethod
    def CreateFromDOM (cls, node, **kw):
        namespace_context = pyxb.namespace.NamespaceContext.GetNodeContext(node)
        assert xsd.nodeIsNamed(node, 'any', 'anyAttribute')
        nc = domutils.NodeAttribute(node, 'namespace')
        if nc is None:
            namespace_constraint = cls.NC_any
        else:
            if cls.NC_any == nc:
                namespace_constraint = cls.NC_any
            elif cls.NC_not == nc:
                namespace_constraint = ( cls.NC_not, namespace_context.targetNamespace() )
            else:
                ncs = set()
                for ns_uri in nc.split():
                    if cls.NC_local == ns_uri:
                        ncs.add(None)
                    elif cls.NC_targetNamespace == ns_uri:
                        ncs.add(namespace_context.targetNamespace())
                    else:
                        ncs.add(pyxb.namespace.NamespaceForURI(ns_uri, create_if_missing=True))
                namespace_constraint = frozenset(ncs)

        pc = domutils.NodeAttribute(node, 'processContents')
        if pc is None:
            process_contents = cls.PC_strict
        else:
            if pc in [ cls.PC_skip, cls.PC_lax, cls.PC_strict ]:
                process_contents = pc
            else:
                raise pyxb.SchemaValidationError('illegal value "%s" for any processContents attribute' % (pc,))

        rv = cls(node=node, namespace_constraint=namespace_constraint, process_contents=process_contents, **kw)
        rv._annotationFromDOM(node)
        return rv

# 3.11.1
class IdentityConstraintDefinition (_SchemaComponent_mixin, _NamedComponent_mixin, _Annotated_mixin, pyxb.namespace.resolution._Resolvable_mixin):
    """An XMLSchema U{Identity Constraint Definition<http://www.w3.org/TR/xmlschema-1/#cIdentity-constraint_Definitions>} component."""

    ICC_KEY = 0x01
    ICC_KEYREF = 0x02
    ICC_UNIQUE = 0x04

    __identityConstraintCategory = None
    def identityConstraintCategory (self):
        return self.__identityConstraintCategory

    __selector = None
    def selector (self):
        return self.__selector

    __fields = None
    def fields (self):
        return self.__fields

    __referencedKey = None
    __referAttribute = None
    __icc = None

    __annotations = None
    def annotations (self):
        return self.__annotations

    # CFD:ICD CFD:IdentityConstraintDefinition
    @classmethod
    def CreateFromDOM (cls, node, **kw):
        name = domutils.NodeAttribute(node, 'name')
        scope = kw['scope']
        assert _ScopedDeclaration_mixin.ScopeIsIndeterminate(scope) or _ScopedDeclaration_mixin.IsValidScope(scope)
        rv = cls(name=name, node=node, **kw)

        kw.pop('node', None)
        kw['owner'] = rv

        #self._annotationFromDOM(node)
        rv.__isResolved = True
        icc = None
        if xsd.nodeIsNamed(node, 'key'):
            icc = rv.ICC_KEY
        elif xsd.nodeIsNamed(node, 'keyref'):
            icc = rv.ICC_KEYREF
            rv.__referAttribute = domutils.NodeAttribute(node, 'refer')
            if rv.__referAttribute is None:
                raise pyxb.SchemaValidationError('Require refer attribute on keyref elements')
            rv.__isResolved = False
        elif xsd.nodeIsNamed(node, 'unique'):
            icc = rv.ICC_UNIQUE
        else:
            raise pyxb.LogicError('Unexpected identity constraint node %s' % (node.toxml("utf-8"),))
        rv.__icc = icc

        cn = domutils.LocateUniqueChild(node, 'selector')
        rv.__selector = domutils.NodeAttribute(cn, 'xpath')
        if rv.__selector is None:
            raise pyxb.SchemaValidationError('selector element missing xpath attribute')

        rv.__fields = []
        for cn in domutils.LocateMatchingChildren(node, 'field'):
            xp_attr = domutils.NodeAttribute(cn, 'xpath')
            if xp_attr is None:
                raise pyxb.SchemaValidationError('field element missing xpath attribute')
            rv.__fields.append(xp_attr)

        rv._annotationFromDOM(node)
        rv.__annotations = []
        if rv.annotation() is not None:
            rv.__annotations.append(rv)

        for cn in node.childNodes:
            if (Node.ELEMENT_NODE != cn.nodeType):
                continue
            an = None
            if xsd.nodeIsNamed(cn, 'selector', 'field'):
                an = domutils.LocateUniqueChild(cn, 'annotation')
            elif xsd.nodeIsNamed(cn, 'annotation'):
                an = cn
            if an is not None:
                rv.__annotations.append(Annotation.CreateFromDOM(an, **kw))

        rv.__identityConstraintCategory = icc
        if rv.ICC_KEYREF != rv.__identityConstraintCategory:
            rv._namespaceContext().targetNamespace().addCategoryObject('identityConstraintDefinition', rv.name(), rv)

        if not rv.isResolved():
            rv._queueForResolution('creation')
        return rv

    __isResolved = False
    def isResolved (self):
        return self.__isResolved

    # res:ICD res:IdentityConstraintDefinition
    def _resolve (self):
        if self.isResolved():
            return self

        icc = self.__icc
        if self.ICC_KEYREF == icc:
            refer_en = self._namespaceContext().interpretQName(self.__referAttribute)
            refer = refer_en.identityConstraintDefinition()
            if refer is None:
                self._queueForResolution('Identity constraint definition %s cannot be found' % (refer_en,), depends_on=refer)
                return self
            self.__referencedKey = refer
        self.__isResolved = True
        return self

    # bR:ICD
    def _bindingRequires_vx (self, include_lax):
        """Constraint definitions that are by reference require the referenced constraint."""
        rv = set()
        if include_lax and (self.__referencedKey is not None):
            rv.add(self.__referencedKey)
        return frozenset(rv)



# 3.12.1
class NotationDeclaration (_SchemaComponent_mixin, _NamedComponent_mixin, _Annotated_mixin):
    """An XMLSchema U{Notation Declaration<http://www.w3.org/TR/xmlschema-1/#cNotation_Declarations>} component."""
    __systemIdentifier = None
    def systemIdentifier (self):
        return self.__systemIdentifier

    __publicIdentifier = None
    def publicIdentifier (self):
        return self.__publicIdentifier

    # CFD:ND CFD:NotationDeclaration
    @classmethod
    def CreateFromDOM (cls, node, **kw):
        name = domutils.NodeAttribute(node, 'name')
        rv = cls(name=name, node=node, **kw)

        rv.__systemIdentifier = domutils.NodeAttribute(node, 'system')
        rv.__publicIdentifier = domutils.NodeAttribute(node, 'public')

        rv._annotationFromDOM(node)
        return rv

    # bR:ND
    def _bindingRequires_vx (self, include_lax):
        return frozenset()

# 3.13.1
class Annotation (_SchemaComponent_mixin):
    """An XMLSchema U{Annotation<http://www.w3.org/TR/xmlschema-1/#cAnnotation>} component."""

    __applicationInformation = None
    def applicationInformation (self):
        return self.__applicationInformation

    __userInformation = None
    def userInformation (self):
        return self.__userInformation

    # Define so superclasses can take keywords
    def __init__ (self, **kw):
        application_information = kw.pop('application_information', None)
        user_information = kw.pop('user_information', None)
        super(Annotation, self).__init__(**kw)
        if (user_information is not None) and (not isinstance(user_information, list)):
            user_information = [ six.text_type(user_information) ]
        if (application_information is not None) and (not isinstance(application_information, list)):
            application_information = [ six.text_type(application_information) ]
        self.__userInformation = user_information
        self.__applicationInformation = application_information

    # @todo: what the hell is this?  From 3.13.2, I think it's a place
    # to stuff attributes from the annotation element, which makes
    # sense, as well as from the annotation's parent element, which
    # doesn't.  Apparently it's for attributes that don't belong to
    # the XMLSchema namespace; so maybe we're not supposed to add
    # those to the other components.  Note that these are attribute
    # information items, not attribute uses.
    __attributes = None

    # CFD:Annotation
    @classmethod
    def CreateFromDOM (cls, node, **kw):
        rv = cls(node=node, **kw)

        # @todo:: Scan for attributes in the node itself that do not
        # belong to the XMLSchema namespace.

        # Node should be an XMLSchema annotation node
        assert xsd.nodeIsNamed(node, 'annotation')
        app_info = []
        user_info = []
        for cn in node.childNodes:
            if xsd.nodeIsNamed(cn, 'appinfo'):
                app_info.append(cn)
            elif xsd.nodeIsNamed(cn, 'documentation'):
                user_info.append(cn)
            else:
                pass
        if 0 < len(app_info):
            rv.__applicationInformation = app_info
        if 0 < len(user_info):
            rv.__userInformation = user_info

        return rv

    __RemoveMultiQuote_re = re.compile('""+')
    def asDocString (self):
        """Return the text in a form suitable for embedding in a
        triple-double-quoted docstring.

        Any sequence of two or more double quotes is replaced by a sequence of
        single quotes that is the same length.  Following this, spaces are
        added at the start and the end as necessary to ensure a double quote
        does not appear in those positions."""
        rv = self.text()
        rv = self.__RemoveMultiQuote_re.sub(lambda _mo: "'" * (_mo.end(0) - _mo.start(0)), rv)
        if rv.startswith('"'):
            rv = ' ' + rv
        if rv.endswith('"'):
            rv = rv + ' '
        return rv

    def text (self):
        if self.__userInformation is None:
            return ''
        text = []
        # Values in userInformation are DOM "documentation" elements.
        # We want their combined content.
        for dn in self.__userInformation:
            for cn in dn.childNodes:
                if Node.TEXT_NODE == cn.nodeType:
                    text.append(cn.data)
        return ''.join(text)

    def __str__ (self):
        """Return the catenation of all user information elements in the
        annotation as a single unicode string.  Returns the empty string if
        there are no user information elements."""
        return self.text()

# Section 3.14.
class SimpleTypeDefinition (_SchemaComponent_mixin, _NamedComponent_mixin, pyxb.namespace.resolution._Resolvable_mixin, _Annotated_mixin):
    """An XMLSchema U{Simple Type Definition<http://www.w3.org/TR/xmlschema-1/#Simple_Type_Definitions>} component."""

    # Reference to the SimpleTypeDefinition on which this is based.
    # The value must be non-None except for the simple ur-type
    # definition.
    __baseTypeDefinition = None
    def baseTypeDefinition (self):
        return self.__baseTypeDefinition

    __memberTypes = None
    __itemTypeExpandedName = None
    __baseExpandedName = None
    __memberTypesExpandedNames = None
    __localFacets = None

    # A map from a subclass of facets.Facet to an instance of that class.
    # Presence of a facet class as a key in this map is the indicator that the
    # type definition and its subtypes are permitted to use the corresponding
    # facet.  All facets in force for this type are present in the map,
    # including those constraints inherited parent types.
    __facets = None
    def facets (self):
        assert (self.__facets is None) or isinstance(self.__facets, six.dictionary_type)
        return self.__facets

    # The facets.FundamentalFacet instances that describe this type
    __fundamentalFacets = None
    def fundamentalFacets (self):
        """A frozenset of instances of facets.FundamentallFacet."""
        return self.__fundamentalFacets

    STD_empty = 0          #<<< Marker indicating an empty set of STD forms
    STD_extension = 0x01   #<<< Representation for extension in a set of STD forms
    STD_list = 0x02        #<<< Representation for list in a set of STD forms
    STD_restriction = 0x04 #<<< Representation of restriction in a set of STD forms
    STD_union = 0x08       #<<< Representation of union in a set of STD forms

    _STD_Map = { 'extension' : STD_extension
               , 'list' : STD_list
               , 'restriction' : STD_restriction
               , 'union' : STD_union }

    # Bitmask defining the subset that comprises the final property
    __final = STD_empty
    @classmethod
    def _FinalToString (cls, final_value):
        """Convert a final value to a string."""
        tags = []
        if final_value & cls.STD_extension:
            tags.append('extension')
        if final_value & cls.STD_list:
            tags.append('list')
        if final_value & cls.STD_restriction:
            tags.append('restriction')
        if final_value & cls.STD_union:
            tags.append('union')
        return ' '.join(tags)

    VARIETY_absent = 0x01       #<<< Only used for the ur-type
    VARIETY_atomic = 0x02       #<<< Use for types based on a primitive type
    VARIETY_list = 0x03         #<<< Use for lists of atomic-variety types
    VARIETY_union = 0x04        #<<< Use for types that aggregate other types

    # Derivation alternative
    _DA_empty = 'none specified'
    _DA_restriction = 'restriction'
    _DA_list = 'list'
    _DA_union = 'union'

    def _derivationAlternative (self):
        return self.__derivationAlternative
    __derivationAlternative = None

    # Identify the sort of value collection this holds.  This field is
    # used to identify unresolved definitions.
    __variety = None
    def variety (self):
        return self.__variety
    @classmethod
    def VarietyToString (cls, variety):
        """Convert a variety value to a string."""
        if cls.VARIETY_absent == variety:
            return 'absent'
        if cls.VARIETY_atomic == variety:
            return 'atomic'
        if cls.VARIETY_list == variety:
            return 'list'
        if cls.VARIETY_union == variety:
            return 'union'
        return '?NoVariety?'

    # For atomic variety only, the root (excepting ur-type) type.
    __primitiveTypeDefinition = None
    def primitiveTypeDefinition (self, throw_if_absent=True):
        if throw_if_absent:
            assert self.VARIETY_atomic == self.variety()
            if self.__primitiveTypeDefinition is None:
                raise pyxb.LogicError('Expected primitive type for %s in %s', self, self.targetNamespace())
        return self.__primitiveTypeDefinition

    # For list variety only, the type of items in the list
    __itemTypeDefinition = None
    def itemTypeDefinition (self):
        assert self.VARIETY_list == self.variety()
        if self.__itemTypeDefinition is None:
            raise pyxb.LogicError('Expected item type')
        return self.__itemTypeDefinition

    # For union variety only, the sequence of candidate members
    __memberTypeDefinitions = None
    def memberTypeDefinitions (self):
        assert self.VARIETY_union == self.variety()
        if self.__memberTypeDefinitions is None:
            raise pyxb.LogicError('Expected member types')
        return self.__memberTypeDefinitions

    # bR:STD
    def _bindingRequires_vx (self, include_lax):
        """Implement base class method.

        This STD depends on its baseTypeDefinition, unless its variety
        is absent.  Other dependencies are on item, primitive, or
        member type definitions."""
        type_definitions = set()
        if self != self.baseTypeDefinition():
            type_definitions.add(self.baseTypeDefinition())
        if self.VARIETY_absent == self.variety():
            type_definitions = set()
        elif self.VARIETY_atomic == self.variety():
            if self != self.primitiveTypeDefinition():
                type_definitions.add(self.primitiveTypeDefinition())
        elif self.VARIETY_list == self.variety():
            assert self != self.itemTypeDefinition()
            type_definitions.add(self.itemTypeDefinition())
        else:
            assert self.VARIETY_union == self.variety()
            assert self not in self.memberTypeDefinitions()
            type_definitions.update(self.memberTypeDefinitions())
        # NB: This type also depends on the value type definitions for
        # any facets that apply to it.  This fact only matters when
        # generating the datatypes_facets source.  That, and the fact
        # that there are dependency loops (e.g., integer requires a
        # nonNegativeInteger for its length facet) means we don't
        # bother adding in those.
        return frozenset(type_definitions)

    # A non-property field that holds a reference to the DOM node from
    # which the type is defined.  The value is held only between the
    # point where the simple type definition instance is created until
    # the point it is resolved.
    __domNode = None

    # Indicate that this instance was defined as a built-in rather
    # than from a DOM instance.
    __isBuiltin = False

    # Allocate one of these.  Users should use one of the Create*
    # factory methods instead.

    def __init__ (self, *args, **kw):
        super(SimpleTypeDefinition, self).__init__(*args, **kw)
        self.__variety = kw['variety']

    def __setstate__ (self, state):
        """Extend base class unpickle support to retain link between
        this instance and the Python class that it describes.

        This is because the pythonSupport value is a class reference,
        not an instance reference, so it wasn't deserialized, and its
        class member link was never set.
        """
        super_fn = getattr(super(SimpleTypeDefinition, self), '__setstate__', lambda _state: self.__dict__.update(_state))
        super_fn(state)
        if self.__pythonSupport is not None:
            self.__pythonSupport._SimpleTypeDefinition(self)

    def __str__ (self):
        if self.name() is not None:
            elts = [ self.name(), ':' ]
        else:
            elts = [ '<anonymous>:' ]
        if self.VARIETY_absent == self.variety():
            elts.append('the ur-type')
        elif self.VARIETY_atomic == self.variety():
            elts.append('restriction of %s' % (self.baseTypeDefinition().name(),))
        elif self.VARIETY_list == self.variety():
            elts.append('list of %s' % (self.itemTypeDefinition().name(),))
        elif self.VARIETY_union == self.variety():
            elts.append('union of %s' % (six.u(' ').join([six.text_type(_mtd.name()) for _mtd in self.memberTypeDefinitions()],)))
        else:
            # Gets here if the type has not been resolved.
            elts.append('?')
            #raise pyxb.LogicError('Unexpected variety %s' % (self.variety(),))
        if self.__facets:
            felts = []
            for (k, v) in six.iteritems(self.__facets):
                if v is not None:
                    felts.append(six.text_type(v))
            elts.append(six.u('\n  %s') % (','.join(felts),))
        if self.__fundamentalFacets:
            elts.append("\n  ")
            elts.append(six.u(',').join( [six.text_type(_f) for _f in self.__fundamentalFacets ]))
        return 'STD[%s]' % (''.join(elts),)

    def _updateFromOther_csc (self, other):
        """Override fields in this instance with those from the other.

        This method is invoked only by Schema._addNamedComponent, and
        then only when a built-in type collides with a schema-defined
        type.  Material like facets is not (currently) held in the
        built-in copy, so the DOM information is copied over to the
        built-in STD, which is subsequently re-resolved.

        Returns self.
        """
        assert self != other
        assert self.isNameEquivalent(other)
        super(SimpleTypeDefinition, self)._updateFromOther_csc(other)

        # The other STD should be an unresolved schema-defined type.
        assert other.__baseTypeDefinition is None, 'Update from resolved STD %s' % (other,)
        assert other.__domNode is not None
        self.__domNode = other.__domNode

        # Preserve the python support
        if other.__pythonSupport is not None:
            # @todo: ERROR multiple references
            self.__pythonSupport = other.__pythonSupport

        # Mark this instance as unresolved so it is re-examined
        self.__variety = None
        return self

    def isBuiltin (self):
        """Indicate whether this simple type is a built-in type."""
        return self.__isBuiltin

    __SimpleUrTypeDefinition = None
    @classmethod
    def SimpleUrTypeDefinition (cls, schema=None, in_builtin_definition=False):
        """Create the SimpleTypeDefinition instance that approximates the simple ur-type.

        See section 3.14.7."""

        #if in_builtin_definition and (cls.__SimpleUrTypeDefinition is not None):
        #    raise pyxb.LogicError('Multiple definitions of SimpleUrType')
        if cls.__SimpleUrTypeDefinition is None:
            # Note: We use a singleton subclass
            assert schema is not None

            ns_ctx = schema.targetNamespace().initialNamespaceContext()

            kw = { 'name' : 'anySimpleType',
                   'schema' : schema,
                   'namespace_context' : ns_ctx,
                   'binding_namespace' : schema.targetNamespace(),
                   'variety' : cls.VARIETY_absent,
                   'scope' : _ScopedDeclaration_mixin.SCOPE_global }
            bi = _SimpleUrTypeDefinition(**kw)
            bi._setPythonSupport(datatypes.anySimpleType)

            # The baseTypeDefinition is the ur-type.
            bi.__baseTypeDefinition = ComplexTypeDefinition.UrTypeDefinition()
            bi.__derivationAlternative = cls._DA_restriction
            # The simple ur-type has an absent variety, not an atomic
            # variety, so does not have a primitiveTypeDefinition

            # No facets on the ur type
            bi.__facets = {}
            bi.__fundamentalFacets = frozenset()

            bi.__resolveBuiltin()

            cls.__SimpleUrTypeDefinition = bi
        return cls.__SimpleUrTypeDefinition

    @classmethod
    def _CreateXMLInstance (cls, name, schema):
        """Create STD instances for built-in types.

        For example, xml:space is a restriction of NCName; xml:lang is a union.

        """
        from pyxb.binding import xml_
        kw = { 'schema' : schema,
               'binding_namespace' : schema.targetNamespace(),
               'namespace_context' : schema.targetNamespace().initialNamespaceContext(),
               'scope' : _ScopedDeclaration_mixin.SCOPE_global,
               'variety' : cls.VARIETY_atomic }
        if 'space' == name:
            bi = cls(**kw)
            bi.__derivationAlternative = cls._DA_restriction
            bi.__baseTypeDefinition = datatypes.NCName.SimpleTypeDefinition()
            bi.__primitiveTypeDefinition = bi.__baseTypeDefinition.__primitiveTypeDefinition
            bi._setPythonSupport(xml_.STD_ANON_space)
            bi.setNameInBinding('STD_ANON_space')
        elif 'lang' == name:
            bi = cls(**kw)
            bi.__baseTypeDefinition = cls.SimpleUrTypeDefinition()
            bi.__memberTypes = [ datatypes.language.SimpleTypeDefinition() ]
            bi.__derivationAlternative = cls._DA_union
            bi.__primitiveTypeDefinition = bi
            bi._setPythonSupport(xml_.STD_ANON_lang)
            bi.setNameInBinding('STD_ANON_lang')
        else:
            raise pyxb.IncompleteImplementationError('No implementation for xml:%s' % (name,))
        bi.__facets = { }
        for v in six.itervalues(bi.pythonSupport().__dict__):
            if isinstance(v, facets.ConstrainingFacet):
                bi.__facets[v.__class__] = v
        return bi

    @classmethod
    def CreatePrimitiveInstance (cls, name, schema, python_support):
        """Create a primitive simple type in the target namespace.

        This is mainly used to pre-load standard built-in primitive
        types, such as those defined by XMLSchema Datatypes.  You can
        use it for your own schemas as well, if you have special types
        that require explicit support to for Pythonic conversion.

        All parameters are required and must be non-None.
        """

        kw = { 'name' : name,
               'schema' : schema,
               'binding_namespace' : schema.targetNamespace(),
               'namespace_context' : schema.targetNamespace().initialNamespaceContext(),
               'scope' : _ScopedDeclaration_mixin.SCOPE_global,
               'variety' : cls.VARIETY_atomic }

        bi = cls(**kw)
        bi._setPythonSupport(python_support)

        # Primitive types are based on the ur-type, and have
        # themselves as their primitive type definition.
        bi.__derivationAlternative = cls._DA_restriction
        bi.__baseTypeDefinition = cls.SimpleUrTypeDefinition()
        bi.__primitiveTypeDefinition = bi

        # Primitive types are built-in
        bi.__resolveBuiltin()
        assert bi.isResolved()
        return bi

    @classmethod
    def CreateDerivedInstance (cls, name, schema, parent_std, python_support):
        """Create a derived simple type in the target namespace.

        This is used to pre-load standard built-in derived types.  You
        can use it for your own schemas as well, if you have special
        types that require explicit support to for Pythonic
        conversion.
        """
        assert parent_std
        assert parent_std.__variety in (cls.VARIETY_absent, cls.VARIETY_atomic)
        kw = { 'name' : name,
               'schema' : schema,
               'binding_namespace' : schema.targetNamespace(),
               'namespace_context' : schema.targetNamespace().initialNamespaceContext(),
               'scope' : _ScopedDeclaration_mixin.SCOPE_global,
               'variety' : parent_std.__variety }

        bi = cls(**kw)
        bi._setPythonSupport(python_support)

        # We were told the base type.  If this is atomic, we re-use
        # its primitive type.  Note that these all may be in different
        # namespaces.
        bi.__baseTypeDefinition = parent_std
        bi.__derivationAlternative = cls._DA_restriction
        if cls.VARIETY_atomic == bi.__variety:
            bi.__primitiveTypeDefinition = bi.__baseTypeDefinition.__primitiveTypeDefinition

        # Derived types are built-in
        bi.__resolveBuiltin()
        return bi

    @classmethod
    def CreateListInstance (cls, name, schema, item_std, python_support):
        """Create a list simple type in the target namespace.

        This is used to preload standard built-in list types.  You can
        use it for your own schemas as well, if you have special types
        that require explicit support to for Pythonic conversion; but
        note that such support is identified by the item_std.
        """

        kw = { 'name' : name,
               'schema' : schema,
               'binding_namespace' : schema.targetNamespace(),
               'namespace_context' : schema.targetNamespace().initialNamespaceContext(),
               'scope' : _ScopedDeclaration_mixin.SCOPE_global,
               'variety' : cls.VARIETY_list }
        bi = cls(**kw)
        bi._setPythonSupport(python_support)

        # The base type is the ur-type.  We were given the item type.
        bi.__baseTypeDefinition = cls.SimpleUrTypeDefinition()
        assert item_std
        bi.__itemTypeDefinition = item_std

        # List types are built-in
        bi.__resolveBuiltin()
        return bi

    @classmethod
    def CreateUnionInstance (cls, name, schema, member_stds):
        """(Placeholder) Create a union simple type in the target namespace.

        This function has not been implemented."""
        raise pyxb.IncompleteImplementationError('No support for built-in union types')

    def __singleSimpleTypeChild (self, body, other_elts_ok=False):
        simple_type_child = None
        for cn in body.childNodes:
            if (Node.ELEMENT_NODE == cn.nodeType):
                if not xsd.nodeIsNamed(cn, 'simpleType'):
                    if other_elts_ok:
                        continue
                    raise pyxb.SchemaValidationError('Context requires element to be xs:simpleType')
                assert not simple_type_child
                simple_type_child = cn
        if simple_type_child is None:
            raise pyxb.SchemaValidationError('Content requires an xs:simpleType member (or a base attribute)')
        return simple_type_child

    # The __initializeFrom* methods are responsible for identifying
    # the variety and the baseTypeDefinition.  The remainder of the
    # resolution is performed by the __completeResolution method.
    # Note that in some cases resolution might yet be premature, so
    # variety is not saved until it is complete.  All this stuff is
    # from section 3.14.2.

    def __initializeFromList (self, body, **kw):
        self.__baseTypeDefinition = self.SimpleUrTypeDefinition()
        self.__itemTypeExpandedName = domutils.NodeAttributeQName(body, 'itemType')
        if self.__itemTypeExpandedName is None:
            # NOTE: The newly created anonymous item type will
            # not be resolved; the caller needs to handle
            # that.
            self.__itemTypeDefinition = self.CreateFromDOM(self.__singleSimpleTypeChild(body), **kw)
        return self.__completeResolution(body, self.VARIETY_list, self._DA_list)

    def __initializeFromRestriction (self, body, **kw):
        if self.__baseTypeDefinition is None:
            self.__baseExpandedName = domutils.NodeAttributeQName(body, 'base')
            if self.__baseExpandedName is None:
                self.__baseTypeDefinition = self.CreateFromDOM(self.__singleSimpleTypeChild(body, other_elts_ok=True), **kw)
        return self.__completeResolution(body, None, self._DA_restriction)

    __localMemberTypes = None
    def __initializeFromUnion (self, body, **kw):
        self.__baseTypeDefinition = self.SimpleUrTypeDefinition()
        mta = domutils.NodeAttribute(body, 'memberTypes')
        self.__memberTypesExpandedNames = None
        if mta is not None:
            nsc = pyxb.namespace.NamespaceContext.GetNodeContext(body)
            self.__memberTypesExpandedNames = [ nsc.interpretQName(_mten) for _mten in mta.split() ]
        if self.__localMemberTypes is None:
            self.__localMemberTypes = []
            for cn in body.childNodes:
                if (Node.ELEMENT_NODE == cn.nodeType) and xsd.nodeIsNamed(cn, 'simpleType'):
                    self.__localMemberTypes.append(self.CreateFromDOM(cn, **kw))
        return self.__completeResolution(body, self.VARIETY_union, self._DA_union)

    def __resolveBuiltin (self):
        if self.hasPythonSupport():
            self.__facets = { }
            for v in six.itervalues(self.pythonSupport().__dict__):
                if isinstance(v, facets.ConstrainingFacet):
                    self.__facets[v.__class__] = v
                    if v.ownerTypeDefinition() is None:
                        v.setFromKeywords(_constructor=True, owner_type_definition=self)
        self.__isBuiltin = True
        return self

    def __defineDefaultFacets (self, variety):
        """Create facets for varieties that can take facets that are undeclared.

        This means unions, which per section 4.1.2.3 of
        http://www.w3.org/TR/xmlschema-2/ can have enumeration or
        pattern restrictions."""
        if self.VARIETY_union != variety:
            return self
        self.__facets.setdefault(facets.CF_pattern)
        self.__facets.setdefault(facets.CF_enumeration)
        return self

    def __processHasFacetAndProperty (self, variety):
        """Identify the facets and properties for this stype.

        This method simply identifies the facets that apply to this
        specific type, and records property values.  Only
        explicitly-associated facets and properties are stored; others
        from base types will also affect this type.  The information
        is taken from the applicationInformation children of the
        definition's annotation node, if any.  If there is no support
        for the XMLSchema_hasFacetAndProperty namespace, this is a
        no-op.

        Upon return, self.__facets is a map from the class for an
        associated fact to None, and self.__fundamentalFacets is a
        frozenset of instances of FundamentalFacet.

        The return value is self.
        """
        self.__facets = { }
        self.__fundamentalFacets = frozenset()
        if self.annotation() is None:
            return self.__defineDefaultFacets(variety)
        app_info = self.annotation().applicationInformation()
        if app_info is  None:
            return self.__defineDefaultFacets(variety)
        facet_map = { }
        fundamental_facets = set()
        seen_facets = set()
        for ai in app_info:
            for cn in ai.childNodes:
                if Node.ELEMENT_NODE != cn.nodeType:
                    continue
                if pyxb.namespace.XMLSchema_hfp.nodeIsNamed(cn, 'hasFacet'):
                    facet_name = domutils.NodeAttribute(cn, 'name')# , pyxb.namespace.XMLSchema_hfp)
                    if facet_name is None:
                        raise pyxb.SchemaValidationError('hasFacet missing name attribute in %s' % (cn,))
                    if facet_name in seen_facets:
                        raise pyxb.SchemaValidationError('Multiple hasFacet specifications for %s' % (facet_name,))
                    seen_facets.add(facet_name)
                    facet_class = facets.ConstrainingFacet.ClassForFacet(facet_name)
                    #facet_map[facet_class] = facet_class(base_type_definition=self)
                    facet_map[facet_class] = None
                if pyxb.namespace.XMLSchema_hfp.nodeIsNamed(cn, 'hasProperty'):
                    fundamental_facets.add(facets.FundamentalFacet.CreateFromDOM(cn, self))
        if 0 < len(facet_map):
            assert self.__baseTypeDefinition == self.SimpleUrTypeDefinition()
            self.__facets = facet_map
            assert isinstance(self.__facets, six.dictionary_type)
        if 0 < len(fundamental_facets):
            self.__fundamentalFacets = frozenset(fundamental_facets)
        return self

    # NB: Must be done after resolution of the base type
    def __updateFacets (self, body):

        # Create local list consisting of facet classes matched in children
        # and the map of keywords used to initialize the local instance.

        local_facets = {}
        for fc in facets.Facet.Facets:
            children = domutils.LocateMatchingChildren(body, fc.Name())
            if 0 < len(children):
                fi = fc(base_type_definition=self.__baseTypeDefinition,
                        owner_type_definition=self)
                if isinstance(fi, facets._LateDatatype_mixin):
                    fi.bindValueDatatype(self)
                for cn in children:
                    kw = { 'annotation': domutils.LocateUniqueChild(cn, 'annotation') }
                    for ai in range(0, cn.attributes.length):
                        attr = cn.attributes.item(ai)
                        # Convert name from unicode to string
                        kw[six.text_type(attr.localName)] = attr.value
                    try:
                        fi.setFromKeywords(**kw)
                    except pyxb.PyXBException as e:
                        raise pyxb.SchemaValidationError('Error assigning facet %s in %s: %s' % (fc.Name(), self.expandedName(), e))
                local_facets[fc] = fi
        self.__localFacets = local_facets

        # We want a map from the union of the facet classes from this STD up
        # through its baseTypeDefinition (if present).  Map elements should be
        # to None if the facet has not been constrained, or to the nearest
        # ConstrainingFacet instance if it is.  ConstrainingFacet instances
        # created for local constraints also need a pointer to the
        # corresponding facet from the ancestor type definition, because those
        # constraints also affect this type.
        base_facets = {}

        # Built-ins didn't get their facets() setting configured, so use the
        # _FacetMap() instead.
        if self.__baseTypeDefinition.isBuiltin():
            pstd = self.__baseTypeDefinition.pythonSupport()
            if pstd != datatypes.anySimpleType:
                base_facets.update(pstd._FacetMap())
        elif self.__baseTypeDefinition.facets():
            assert isinstance(self.__baseTypeDefinition.facets(), six.dictionary_type)
            base_facets.update(self.__baseTypeDefinition.facets())
        base_facets.update(self.facets())

        self.__facets = self.__localFacets
        for fc in six.iterkeys(base_facets):
            self.__facets.setdefault(fc, base_facets[fc])
        assert isinstance(self.__facets, six.dictionary_type)

    def _createRestriction (self, owner, body):
        """Create a new simple type with this as its base.

        The type is owned by the provided owner, and may have facet
        restrictions defined by the body.
        @param owner: the owner for the newly created type
        @type owner: L{ComplexTypeDefinition}
        @param body: the DOM node from which facet information will be extracted
        @type body: C{xml.dom.Node}
        @rtype: L{SimpleTypeDefinition}
        """
        std = SimpleTypeDefinition(owner=owner, namespace_context=owner._namespaceContext(), variety=None, scope=self._scope(), schema=owner._schema())
        std.__baseTypeDefinition = self
        return std.__completeResolution(body, None, self._DA_restriction)

    # Complete the resolution of some variety of STD.  Note that the
    # variety is compounded by an alternative, since there is no
    # 'restriction' variety.
    def __completeResolution (self, body, variety, alternative):
        assert self.__variety is None
        if self.__baseTypeDefinition is None:
            assert self.__baseExpandedName is not None
            base_type = self.__baseExpandedName.typeDefinition()
            if not isinstance(base_type, SimpleTypeDefinition):
                raise pyxb.SchemaValidationError('Unable to locate base type %s' % (self.__baseExpandedName,))
            self.__baseTypeDefinition = base_type
        # If the base type exists but has not yet been resolved,
        # delay processing this type until the one it depends on
        # has been completed.
        assert self.__baseTypeDefinition != self
        if not self.__baseTypeDefinition.isResolved():
            self._queueForResolution('base type %s is not resolved' % (self.__baseTypeDefinition,), depends_on=self.__baseTypeDefinition)
            return self
        if variety is None:
            # 3.14.1 specifies that the variety is the variety of the base
            # type definition which, by the way, can't be the ur type.
            variety = self.__baseTypeDefinition.__variety
        assert variety is not None

        if self.VARIETY_absent == variety:
            # The ur-type is always resolved.  So are restrictions of it,
            # which is how we might get here.
            pass
        elif self.VARIETY_atomic == variety:
            # Atomic types (and their restrictions) use the primitive
            # type, which is the highest type that is below the
            # ur-type (which is not atomic).
            ptd = self
            while isinstance(ptd, SimpleTypeDefinition) and (self.VARIETY_atomic == ptd.__baseTypeDefinition.variety()):
                ptd = ptd.__baseTypeDefinition

            self.__primitiveTypeDefinition = ptd
        elif self.VARIETY_list == variety:
            if self._DA_list == alternative:
                if self.__itemTypeExpandedName is not None:
                    self.__itemTypeDefinition = self.__itemTypeExpandedName.typeDefinition()
                    if not isinstance(self.__itemTypeDefinition, SimpleTypeDefinition):
                        raise pyxb.SchemaValidationError('Unable to locate STD %s for items' % (self.__itemTypeExpandedName,))
            elif self._DA_restriction == alternative:
                self.__itemTypeDefinition = self.__baseTypeDefinition.__itemTypeDefinition
            else:
                raise pyxb.LogicError('completeResolution list variety with alternative %s' % (alternative,))
        elif self.VARIETY_union == variety:
            if self._DA_union == alternative:
                # First time we try to resolve, create the member type
                # definitions.  If something later prevents us from resolving
                # this type, we don't want to create them again, because we
                # might already have references to them.
                if self.__memberTypeDefinitions is None:
                    mtd = []
                    # If present, first extract names from memberTypes,
                    # and add each one to the list
                    if self.__memberTypesExpandedNames is not None:
                        for mn_en in self.__memberTypesExpandedNames:
                            # THROW if type has not been defined
                            std = mn_en.typeDefinition()
                            if std is None:
                                raise pyxb.SchemaValidationError('Unable to locate member type %s' % (mn_en,))
                            # Note: We do not need these to be resolved (here)
                            assert isinstance(std, SimpleTypeDefinition)
                            mtd.append(std)
                    # Now look for local type definitions
                    mtd.extend(self.__localMemberTypes)
                    self.__memberTypeDefinitions = mtd
                    assert None not in self.__memberTypeDefinitions

                # Replace any member types that are themselves unions with the
                # members of those unions, in order.  Note that doing this
                # might indicate we can't resolve this type yet, which is why
                # we separated the member list creation and the substitution
                # phases
                mtd = []
                for mt in self.__memberTypeDefinitions:
                    assert isinstance(mt, SimpleTypeDefinition)
                    if not mt.isResolved():
                        self._queueForResolution('member type not resolved', depends_on=mt)
                        return self
                    if self.VARIETY_union == mt.variety():
                        mtd.extend(mt.memberTypeDefinitions())
                    else:
                        mtd.append(mt)
            elif self._DA_restriction == alternative:
                assert self.__baseTypeDefinition
                # Base type should have been resolved before we got here
                assert self.__baseTypeDefinition.isResolved()
                mtd = self.__baseTypeDefinition.__memberTypeDefinitions
                assert mtd is not None
            else:
                raise pyxb.LogicError('completeResolution union variety with alternative %s' % (alternative,))
            # Save a unique copy
            self.__memberTypeDefinitions = mtd[:]
        else:
            raise pyxb.LogicError('completeResolution with variety 0x%02x' % (variety,))

        # Determine what facets, if any, apply to this type.  This
        # should only do something if this is a primitive type.
        self.__processHasFacetAndProperty(variety)
        try:
            pyxb.namespace.NamespaceContext.PushContext(pyxb.namespace.NamespaceContext.GetNodeContext(body))
            self.__updateFacets(body)
        finally:
            pyxb.namespace.NamespaceContext.PopContext()

        self.__derivationAlternative = alternative
        self.__variety = variety
        self.__domNode = None
        return self

    def isResolved (self):
        """Indicate whether this simple type is fully defined.

        Type resolution for simple types means that the corresponding
        schema component fields have been set.  Specifically, that
        means variety, baseTypeDefinition, and the appropriate
        additional fields depending on variety.  See _resolve() for
        more information.
        """
        # Only unresolved nodes have an unset variety
        return (self.__variety is not None)

    # STD:res
    def _resolve (self):
        """Attempt to resolve the type.

        Type resolution for simple types means that the corresponding
        schema component fields have been set.  Specifically, that
        means variety, baseTypeDefinition, and the appropriate
        additional fields depending on variety.

        All built-in STDs are resolved upon creation.  Schema-defined
        STDs are held unresolved until the schema has been completely
        read, so that references to later schema-defined STDs can be
        resolved.  Resolution is performed after the entire schema has
        been scanned and STD instances created for all
        topLevelSimpleTypes.

        If a built-in STD is also defined in a schema (which it should
        be for XMLSchema), the built-in STD is kept, with the
        schema-related information copied over from the matching
        schema-defined STD.  The former then replaces the latter in
        the list of STDs to be resolved.

        Types defined by restriction have the same variety as the type
        they restrict.  If a simple type restriction depends on an
        unresolved type, this method simply queues it for resolution
        in a later pass and returns.
        """
        if self.__variety is not None:
            return self
        assert self.__domNode
        node = self.__domNode

        kw = { 'owner' : self
              , 'schema' : self._schema() }

        bad_instance = False
        # The guts of the node should be exactly one instance of
        # exactly one of these three types.
        candidate = domutils.LocateUniqueChild(node, 'list')
        if candidate:
            self.__initializeFromList(candidate, **kw)

        candidate = domutils.LocateUniqueChild(node, 'restriction')
        if candidate:
            if self.__variety is None:
                self.__initializeFromRestriction(candidate, **kw)
            else:
                bad_instance = True

        candidate = domutils.LocateUniqueChild(node, 'union')
        if candidate:
            if self.__variety is None:
                self.__initializeFromUnion(candidate, **kw)
            else:
                bad_instance = True

        if self.__baseTypeDefinition is None:
            raise pyxb.SchemaValidationError('xs:simpleType must have list, union, or restriction as child')

        if self._schema() is not None:
            self.__final = self._schema().finalForNode(node, self._STD_Map)

        # It is NOT an error to fail to resolve the type.
        if bad_instance:
            raise pyxb.SchemaValidationError('Expected exactly one of list, restriction, union as child of simpleType')

        return self

    # CFD:STD CFD:SimpleTypeDefinition
    @classmethod
    def CreateFromDOM (cls, node, **kw):
        # Node should be an XMLSchema simpleType node
        assert xsd.nodeIsNamed(node, 'simpleType')

        name = domutils.NodeAttribute(node, 'name')

        rv = cls(name=name, node=node, variety=None, **kw)
        rv._annotationFromDOM(node)

        # Creation does not attempt to do resolution.  Queue up the newly created
        # whatsis so we can resolve it after everything's been read in.
        rv.__domNode = node
        rv._queueForResolution('creation')

        return rv

    # pythonSupport is None, or a subclass of datatypes.simpleTypeDefinition.
    # When set, this simple type definition instance must be uniquely
    # associated with the python support type.
    __pythonSupport = None

    def _setPythonSupport (self, python_support):
        # Includes check that python_support is not None
        assert issubclass(python_support, basis.simpleTypeDefinition)
        # Can't share support instances
        self.__pythonSupport = python_support
        self.__pythonSupport._SimpleTypeDefinition(self)
        if self.nameInBinding() is None:
            self.setNameInBinding(self.__pythonSupport.__name__)
        return self.__pythonSupport

    def hasPythonSupport (self):
        return self.__pythonSupport is not None

    def pythonSupport (self):
        if self.__pythonSupport is None:
            raise pyxb.LogicError('%s: No support defined' % (self.name(),))
        return self.__pythonSupport

    def stringToPython (self, string):
        return self.pythonSupport().stringToPython(string)

    def pythonToString (self, value):
        return self.pythonSupport().pythonToString(value)

class _SimpleUrTypeDefinition (SimpleTypeDefinition, _Singleton_mixin):
    """Subclass ensures there is only one simple ur-type."""
    pass

class _ImportElementInformationItem (_Annotated_mixin):
    """Data associated with an
    U{import<http://www.w3.org/TR/xmlschema-1/#composition-schemaImport>}
    statement within a schema."""

    def id (self):
        """The value of the C{id} attribute from the import statement."""
        return self.__id
    __id = None

    def namespace (self):
        """The L{pyxb.namespace.Namespace} instance corresponding to the value
        of the C{namespace} attribute from the import statement."""
        return self.__namespace
    __namespace = None

    def schemaLocation (self):
        """The value of the C{schemaLocation} attribute from the import
        statement, normalized relative to the location of the importing
        schema."""
        return self.__schemaLocation
    __schemaLocation = None

    def prefix (self):
        """The prefix from a namespace declaration for L{namespace} that was
        active in the context of the import element, or C{None} if there was
        no relevant namespace declaration in scope at that point.

        This is propagated to be used as the default prefix for the
        corresponding namespace if no prefix had been assigned.
        """
        return self.__prefix
    __prefix = None

    def schema (self):
        """The L{Schema} instance corresponding to the imported schema, if
        available.

        Normally C{import} statements will be fulfilled by loading components
        from a L{namespace archive<pyxb.namespace.NamespaceArchive>} in which
        the corresponding namespace is marked as public.  Where there are
        cycles in the namespace dependency graph, or the schema for a
        namespace are associated with a restricted profile of another
        namespace, there may be no such archive and instead the components are
        obtained using this schema."""
        return self.__schema
    __schema = None

    def __init__ (self, importing_schema, node, **kw):
        """Gather the information relative to an C{import} statement.

        If the imported namespace can be loaded from an archive, the
        C{schemaLocation} attribute is ignored.  Otherwise, it attempts to
        retrieve and parse the corresponding schema (if this has not already
        been done).

        @param importing_schema: The L{Schema} instance in which the import
        was found.
        @param node: The C{xml.dom.DOM} node incorporating the schema
        information.

        @raise Exception: Any exception raised when attempting to retrieve and
        parse data from the schema location.
        """

        super(_ImportElementInformationItem, self).__init__(**kw)
        uri = domutils.NodeAttribute(node, 'namespace')
        if uri is None:
            raise pyxb.IncompleteImplementationError('import statements without namespace not supported')
        schema_location = pyxb.utils.utility.NormalizeLocation(domutils.NodeAttribute(node, 'schemaLocation'), importing_schema.location())
        self.__schemaLocation = schema_location
        ns = self.__namespace = pyxb.namespace.NamespaceForURI(uri, create_if_missing=True)
        need_schema = ns.isImportAugmentable()
        if not need_schema:
            # Discard location if we expect to be able to learn about this
            # namespace from an archive or a built-in description
            self.__schemaLocation = None

        ns_ctx = pyxb.namespace.NamespaceContext.GetNodeContext(node)
        if self.schemaLocation() is not None:
            # @todo: NOTICE
            (has_schema, schema_instance) = self.__namespace.lookupSchemaByLocation(schema_location)
            if not has_schema:
                ckw = { 'absolute_schema_location' : schema_location,
                        'generation_uid' : importing_schema.generationUID(),
                        'uri_content_archive_directory' : importing_schema._uriContentArchiveDirectory(),
                        }
                try:
                    schema_instance = Schema.CreateFromLocation(**ckw)
                except Exception:
                    _log.exception('Import %s cannot read schema location %s (%s)', ns, self.__schemaLocation, schema_location)
                    raise
            self.__schema = schema_instance
        elif need_schema:
            _log.warning('No information available on imported namespace %s', uri)

        # If we think we found a schema, make sure it's in the right
        # namespace.
        if self.__schema is not None:
            if ns != self.__schema.targetNamespace():
                raise pyxb.SchemaValidationError('Import expected namespace %s but got %s' % (ns, self.__schema.targetNamespace()))

        self.__prefix = ns_ctx.prefixForNamespace(self.namespace())

        self._annotationFromDOM(node)

class Schema (_SchemaComponent_mixin):
    """An XMLSchema U{Schema<http://www.w3.org/TR/xmlschema-1/#Schemas>}."""

    def __getstate__ (self):
        raise pyxb.LogicError('Attempt to serialize Schema instance')

    # List of annotations
    __annotations = None

    # True when we have started seeing elements, attributes, or
    # notations.
    __pastProlog = False

    def location (self):
        """URI or path to where the schema can be found.

        For schema created by a user, the location should be provided to the
        constructor using the C{schema_location} keyword.  In the case of
        imported or included schema, the including schema's location is used
        as the base URI for determining the absolute URI of the included
        schema from its (possibly relative) location value.  For files,
        the scheme and authority portions are generally absent, as is often
        the abs_path part."""
        return self.__location
    __location = None

    def locationTag (self):
        return self.__locationTag
    __locationTag = None

    def signature (self):
        return self.__signature
    __signature = None

    def generationUID (self):
        return self.__generationUID
    __generationUID = None

    def originRecord (self):
        return self.__originRecord
    __originRecord = None

    def targetNamespace (self):
        """The targetNamespace of a componen.

        This is None, or a reference to a Namespace in which the
        component is declared (either as a global or local to one of
        the namespace's complex type definitions).  This is immutable
        after creation.
        """
        return self.__targetNamespace
    __targetNamespace = None

    def defaultNamespace (self):
        """Default namespace of the schema.

        Will be None unless the schema has an 'xmlns' attribute.  The
        value must currently be provided as a keyword parameter to the
        constructor.  """
        return self.__defaultNamespace
    __defaultNamespace = None

    def referencedNamespaces (self):
        return self.__referencedNamespaces
    __referencedNamespaces = None

    __namespaceData = None

    def importEIIs (self):
        return self.__importEIIs
    __importEIIs = None

    def importedSchema (self):
        return self.__importedSchema
    __importedSchema = None
    def includedSchema (self):
        return self.__includedSchema
    __includedSchema = None

    _QUALIFIED = "qualified"
    _UNQUALIFIED = "unqualified"

    # Default values for standard recognized schema attributes
    __attributeMap = { pyxb.namespace.ExpandedName(None, 'attributeFormDefault') : _UNQUALIFIED
                     , pyxb.namespace.ExpandedName(None, 'elementFormDefault') : _UNQUALIFIED
                     , pyxb.namespace.ExpandedName(None, 'blockDefault') : ''
                     , pyxb.namespace.ExpandedName(None, 'finalDefault') : ''
                     , pyxb.namespace.ExpandedName(None, 'id') : None
                     , pyxb.namespace.ExpandedName(None, 'targetNamespace') : None
                     , pyxb.namespace.ExpandedName(None, 'version') : None
                     , pyxb.namespace.XML.createExpandedName('lang') : None
                     }

    def _setAttributeFromDOM (self, attr):
        """Override the schema attribute with the given DOM value."""
        self.__attributeMap[pyxb.namespace.ExpandedName(attr.name)] = attr.nodeValue
        return self

    def _setAttributesFromMap (self, attr_map):
        """Override the schema attributes with values from the given map."""
        self.__attributeMap.update(attr_map)
        return self

    def schemaHasAttribute (self, attr_name):
        """Return True iff the schema has an attribute with the given (nc)name."""
        if isinstance(attr_name, six.string_types):
            attr_name = pyxb.namespace.ExpandedName(None, attr_name)
        return attr_name in self.__attributeMap

    def schemaAttribute (self, attr_name):
        """Return the schema attribute value associated with the given (nc)name.

        @param attr_name: local name for the attribute in the schema element.
        @return: the value of the corresponding attribute, or C{None} if it
        has not been defined and has no default.
        @raise KeyError: C{attr_name} is not a valid attribute for a C{schema} element.
        """
        if isinstance(attr_name, six.string_types):
            attr_name = pyxb.namespace.ExpandedName(None, attr_name)
        return self.__attributeMap[attr_name]

    __SchemaCategories = ( 'typeDefinition', 'attributeGroupDefinition', 'modelGroupDefinition',
                           'attributeDeclaration', 'elementDeclaration', 'notationDeclaration',
                           'identityConstraintDefinition' )

    def _uriContentArchiveDirectory (self):
        return self.__uriContentArchiveDirectory
    __uriContentArchiveDirectory = None

    def __init__ (self, *args, **kw):
        # Force resolution of available namespaces if not already done
        if not kw.get('_bypass_preload', False):
            pyxb.namespace.archive.NamespaceArchive.PreLoadArchives()

        assert 'schema' not in kw
        self.__uriContentArchiveDirectory = kw.get('uri_content_archive_directory')
        self.__location = kw.get('schema_location')
        if self.__location is not None:
            schema_path = self.__location
            if 0 <= schema_path.find(':'):
                schema_path = urlparse.urlparse(schema_path)[2] # .path
            self.__locationTag = os.path.split(schema_path)[1].split('.')[0]

        self.__generationUID = kw.get('generation_uid')
        if self.__generationUID is None:
            _log.warning('No generationUID provided')
            self.__generationUID = pyxb.utils.utility.UniqueIdentifier()

        self.__signature = kw.get('schema_signature')

        super(Schema, self).__init__(*args, **kw)
        self.__importEIIs = set()
        self.__includedSchema = set()
        self.__importedSchema = set()
        self.__targetNamespace = self._namespaceContext().targetNamespace()
        if not isinstance(self.__targetNamespace, pyxb.namespace.Namespace):
            raise pyxb.LogicError('Schema constructor requires valid Namespace instance as target_namespace')

        # NB: This will raise pyxb.SchemaUniquenessError if it appears this
        # schema has already been incorporated into the target namespace.
        self.__originRecord = self.__targetNamespace.addSchema(self)

        self.__targetNamespace.configureCategories(self.__SchemaCategories)
        if self.__defaultNamespace is not None:
            self.__defaultNamespace.configureCategories(self.__SchemaCategories)

        self.__attributeMap = self.__attributeMap.copy()
        self.__annotations = []
        # @todo: This isn't right if namespaces are introduced deeper in the document
        self.__referencedNamespaces = list(six.itervalues(self._namespaceContext().inScopeNamespaces()))

    __TopLevelComponentMap = {
        'element' : ElementDeclaration,
        'attribute' : AttributeDeclaration,
        'notation' : NotationDeclaration,
        'simpleType' : SimpleTypeDefinition,
        'complexType' : ComplexTypeDefinition,
        'group' : ModelGroupDefinition,
        'attributeGroup' : AttributeGroupDefinition
        }

    @classmethod
    def CreateFromDocument (cls, xmls, **kw):
        if not ('schema_signature' in kw):
            kw['schema_signature'] = pyxb.utils.utility.HashForText(xmls)
        return cls.CreateFromDOM(domutils.StringToDOM(xmls, **kw), **kw)

    @classmethod
    def CreateFromLocation (cls, **kw):
        """Create a schema from a schema location.

        Reads an XML document from the schema location and creates a schema
        using it.  All keyword parameters are passed to L{CreateFromDOM}.

        @keyword schema_location: A file path or a URI.  If this is a relative
        URI and C{parent_uri} is present, the actual location will be
        L{normallzed<pyxb.utils.utility.NormalizeLocation>}.
        @keyword parent_uri: The context within which schema_location will be
        normalized, if necessary.
        @keyword absolute_schema_location: A file path or URI.  This value is
        not normalized, and supersedes C{schema_location}.
        """
        schema_location = kw.pop('absolute_schema_location', pyxb.utils.utility.NormalizeLocation(kw.get('schema_location'), kw.get('parent_uri'), kw.get('prefix_map')))
        kw['location_base'] = kw['schema_location'] = schema_location
        assert isinstance(schema_location, six.string_types), 'Unexpected value %s type %s for schema_location' % (schema_location, type(schema_location))
        uri_content_archive_directory = kw.get('uri_content_archive_directory')
        return cls.CreateFromDocument(pyxb.utils.utility.DataFromURI(schema_location, archive_directory=uri_content_archive_directory), **kw)

    @classmethod
    def CreateFromStream (cls, stream, **kw):
        return cls.CreateFromDocument(stream.read(), **kw)

    @classmethod
    def CreateFromDOM (cls, node, namespace_context=None, schema_location=None, schema_signature=None, generation_uid=None, **kw):
        """Take the root element of the document, and scan its attributes under
        the assumption it is an XMLSchema schema element.  That means
        recognize namespace declarations and process them.  Also look for
        and set the default namespace.  All other attributes are passed up
        to the parent class for storage."""

        # Get the context of any schema that is including (not importing) this
        # one.
        including_context = kw.get('including_context')

        root_node = node
        if Node.DOCUMENT_NODE == node.nodeType:
            root_node = root_node.documentElement
        if Node.ELEMENT_NODE != root_node.nodeType:
            raise pyxb.LogicError('Must be given a DOM node of type ELEMENT')

        assert (namespace_context is None) or isinstance(namespace_context, pyxb.namespace.NamespaceContext)
        ns_ctx = pyxb.namespace.NamespaceContext.GetNodeContext(root_node,
                                                                           parent_context=namespace_context,
                                                                           including_context=including_context)

        tns = ns_ctx.targetNamespace()
        if tns is None:
            raise pyxb.SchemaValidationError('No targetNamespace associated with content (not a schema?)')
        schema = cls(namespace_context=ns_ctx, schema_location=schema_location, schema_signature=schema_signature, generation_uid=generation_uid, **kw)
        schema.__namespaceData = ns_ctx

        if schema.targetNamespace() != ns_ctx.targetNamespace():
            raise pyxb.SchemaValidationError('targetNamespace %s conflicts with %s' % (schema.targetNamespace(), ns_ctx.targetNamespace()))

        # Update the attribute map
        for ai in range(root_node.attributes.length):
            schema._setAttributeFromDOM(root_node.attributes.item(ai))

        # Verify that the root node is an XML schema element
        if not xsd.nodeIsNamed(root_node, 'schema'):
            raise pyxb.SchemaValidationError('Root node %s of document is not an XML schema element' % (root_node.nodeName,))

        for cn in root_node.childNodes:
            if Node.ELEMENT_NODE == cn.nodeType:
                rv = schema.__processTopLevelNode(cn)
                if rv is None:
                    _log.info('Unrecognized: %s %s', cn.nodeName, cn.toxml("utf-8"))
            elif Node.TEXT_NODE == cn.nodeType:
                # Non-element content really should just be whitespace.
                # If something else is seen, print it for inspection.
                text = cn.data.strip()
                if text:
                    _log.info('Ignored text: %s', text)
            elif Node.COMMENT_NODE == cn.nodeType:
                pass
            else:
                # ATTRIBUTE_NODE
                # CDATA_SECTION_NODE
                # ENTITY_NODE
                # PROCESSING_INSTRUCTION
                # DOCUMENT_NODE
                # DOCUMENT_TYPE_NODE
                # NOTATION_NODE
                _log.info('Ignoring non-element: %s', cn)

        # Do not perform resolution yet: we may be done with this schema, but
        # the namespace may incorporate additional ones, and we can't resolve
        # until everything's present.
        return schema

    _SA_All = '#all'

    def __ebvForNode (self, attr, dom_node, candidate_map):
        ebv = domutils.NodeAttribute(dom_node, attr)
        if ebv is None:
            ebv = self.schemaAttribute('%sDefault' % (attr,))
        rv = 0
        if ebv == self._SA_All:
            for v in six.itervalues(candidate_map):
                rv += v
        else:
            for candidate in ebv.split():
                rv += candidate_map.get(candidate, 0)
        return rv

    def blockForNode (self, dom_node, candidate_map):
        """Return a bit mask indicating a set of options read from the node's "block" attribute or the schema's "blockDefault" attribute.

        A value of '#all' means enable every options; otherwise, the attribute
        value should be a list of tokens, for which the corresponding value
        will be added to the return value.

        @param dom_node: the node from which the "block" attribute will be retrieved
        @type dom_node: C{xml.dom.Node}
        @param candidate_map: map from strings to bitmask values
        """
        return self.__ebvForNode('block', dom_node, candidate_map)

    def finalForNode (self, dom_node, candidate_map):
        """Return a bit mask indicating a set of options read from the node's
        "final" attribute or the schema's "finalDefault" attribute.

        A value of '#all' means enable every options; otherwise, the attribute
        value should be a list of tokens, for which the corresponding value
        will be added to the return value.

        @param dom_node: the node from which the "final" attribute will be retrieved
        @type dom_node: C{xml.dom.Node}
        @param candidate_map: map from strings to bitmask values
        """
        return self.__ebvForNode('final', dom_node, candidate_map)

    def targetNamespaceForNode (self, dom_node, declaration_type):
        """Determine the target namespace for a local attribute or element declaration.

        Look at the node's C{form} attribute, or if none the schema's
        C{attributeFormDefault} or C{elementFormDefault} value.  If the
        resulting value is C{"qualified"} and the parent schema has a
        non-absent target namespace, return it to use as the declaration
        target namespace.  Otherwise, return None to indicate that the
        declaration has no namespace.

        @param dom_node: The node defining an element or attribute declaration
        @param declaration_type: Either L{AttributeDeclaration} or L{ElementDeclaration}
        @return: L{pyxb.namespace.Namespace} or None
        """

        form_type = domutils.NodeAttribute(dom_node, 'form')
        if form_type is None:
            if declaration_type == ElementDeclaration:
                form_type = self.schemaAttribute('elementFormDefault')
            elif declaration_type == AttributeDeclaration:
                form_type = self.schemaAttribute('attributeFormDefault')
            else:
                raise pyxb.LogicError('Expected ElementDeclaration or AttributeDeclaration: got %s' % (declaration_type,))
        tns = None
        if (self._QUALIFIED == form_type):
            tns = self.targetNamespace()
            if tns.isAbsentNamespace():
                tns = None
        else:
            if (self._UNQUALIFIED != form_type):
                raise pyxb.SchemaValidationError('Form type neither %s nor %s' % (self._QUALIFIED, self._UNQUALIFIED))
        return tns

    def __requireInProlog (self, node_name):
        """Throw a SchemaValidationException referencing the given
        node if we have passed the sequence point representing the end
        of prolog elements."""

        if self.__pastProlog:
            raise pyxb.SchemaValidationError('Unexpected node %s after prolog' % (node_name,))

    def __processInclude (self, node):
        self.__requireInProlog(node.nodeName)
        # See section 4.2.1 of Structures.
        abs_uri = pyxb.utils.utility.NormalizeLocation(domutils.NodeAttribute(node, 'schemaLocation'), self.__location)
        (has_schema, schema_instance) = self.targetNamespace().lookupSchemaByLocation(abs_uri)
        if not has_schema:
            kw = { 'absolute_schema_location': abs_uri,
                   'including_context': self.__namespaceData,
                   'generation_uid': self.generationUID(),
                   'uri_content_archive_directory': self._uriContentArchiveDirectory(),
                 }
            try:
                schema_instance = self.CreateFromLocation(**kw)
            except pyxb.SchemaUniquenessError as e:
                _log.warning('Skipping apparent redundant inclusion of %s defining %s (hash matches %s)', e.schemaLocation(), e.namespace(), e.existingSchema().location())
            except Exception as e:
                _log.exception('INCLUDE %s caught', abs_uri)
                raise
        if schema_instance:
            if self.targetNamespace() != schema_instance.targetNamespace():
                raise pyxb.SchemaValidationError('Included namespace %s not consistent with including namespace %s' % (schema_instance.targetNamespace(), self.targetNamespace()))
            self.__includedSchema.add(schema_instance)
        return node

    def __processImport (self, node):
        """Process an import directive.

        This attempts to locate schema (named entity) information for
        a namespace that is referenced by this schema.
        """

        self.__requireInProlog(node.nodeName)
        import_eii = _ImportElementInformationItem(self, node)
        if import_eii.schema() is not None:
            self.__importedSchema.add(import_eii.schema())
        self.targetNamespace().importNamespace(import_eii.namespace())
        ins = import_eii.namespace()
        if ins.prefix() is None:
            ins.setPrefix(import_eii.prefix())
        self.__importEIIs.add(import_eii)
        return node

    def __processRedefine (self, node):
        self.__requireInProlog(node.nodeName)
        raise pyxb.IncompleteImplementationError('redefine not implemented')

    def __processAnnotation (self, node):
        self._addAnnotation(Annotation.CreateFromDOM(node))
        return self

    def __processTopLevelNode (self, node):
        """Process a DOM node from the top level of the schema.

        This should return a non-None value if the node was
        successfully recognized."""
        if xsd.nodeIsNamed(node, 'include'):
            return self.__processInclude(node)
        if xsd.nodeIsNamed(node, 'import'):
            return self.__processImport(node)
        if xsd.nodeIsNamed(node, 'redefine'):
            return self.__processRedefine(node)
        if xsd.nodeIsNamed(node, 'annotation'):
            return self.__processAnnotation(node)

        component = self.__TopLevelComponentMap.get(node.localName)
        if component is not None:
            self.__pastProlog = True
            kw = { 'scope' : _ScopedDeclaration_mixin.SCOPE_global,
                   'schema' : self,
                   'owner' : self }
            return self._addNamedComponent(component.CreateFromDOM(node, **kw))

        raise pyxb.SchemaValidationError('Unexpected top-level element %s' % (node.nodeName,))

    def _addAnnotation (self, annotation):
        self.__annotations.append(annotation)
        return annotation

    def _addNamedComponent (self, nc):
        tns = self.targetNamespace()
        assert tns is not None
        if not isinstance(nc, _NamedComponent_mixin):
            raise pyxb.LogicError('Attempt to add unnamed %s instance to dictionary' % (nc.__class__,))
        if nc.isAnonymous():
            raise pyxb.LogicError('Attempt to add anonymous component to dictionary: %s', (nc.__class__,))
        if isinstance(nc, _ScopedDeclaration_mixin):
            assert _ScopedDeclaration_mixin.SCOPE_global == nc.scope()
        if isinstance(nc, (SimpleTypeDefinition, ComplexTypeDefinition)):
            return self.__addTypeDefinition(nc)
        if isinstance(nc, AttributeDeclaration):
            return self.__addAttributeDeclaration(nc)
        if isinstance(nc, AttributeGroupDefinition):
            return self.__addAttributeGroupDefinition(nc)
        if isinstance(nc, ModelGroupDefinition):
            return tns.addCategoryObject('modelGroupDefinition', nc.name(), nc)
        if isinstance(nc, ElementDeclaration):
            return tns.addCategoryObject('elementDeclaration', nc.name(), nc)
        if isinstance(nc, NotationDeclaration):
            return tns.addCategoryObject('notationDeclaration', nc.name(), nc)
        if isinstance(nc, IdentityConstraintDefinition):
            return tns.addCategoryObject('identityConstraintDefinition', nc.name(), nc)
        assert False, 'No support to record named component of type %s' % (nc.__class__,)

    def __addTypeDefinition (self, td):
        local_name = td.name()
        assert self.__targetNamespace
        tns = self.targetNamespace()
        old_td = tns.typeDefinitions().get(local_name)
        if (old_td is not None) and (old_td != td):
            if isinstance(td, ComplexTypeDefinition) != isinstance(old_td, ComplexTypeDefinition):
                raise pyxb.SchemaValidationError('Name %s used for both simple and complex types' % (td.name(),))

            if not old_td._allowUpdateFromOther(td):
                raise pyxb.SchemaValidationError('Attempt to re-define non-builtin type definition %s' % (tns.createExpandedName(local_name),))

            # Copy schema-related information from the new definition
            # into the old one, and continue to use the old one.
            td = tns._replaceComponent(td, old_td._updateFromOther(td))
        else:
            tns.addCategoryObject('typeDefinition', td.name(), td)
        assert td is not None
        return td

    def __addAttributeDeclaration (self, ad):
        local_name = ad.name()
        assert self.__targetNamespace
        tns = self.targetNamespace()
        old_ad = tns.attributeDeclarations().get(local_name)
        if (old_ad is not None) and (old_ad != ad):
            if not old_ad._allowUpdateFromOther(ad):
                raise pyxb.SchemaValidationError('Attempt to re-define non-builtin attribute declaration %s' % (tns.createExpandedName(local_name),))

            # Copy schema-related information from the new definition
            # into the old one, and continue to use the old one.
            ad = tns._replaceComponent(ad, old_ad._updateFromOther(ad))
        else:
            tns.addCategoryObject('attributeDeclaration', ad.name(), ad)
        assert ad is not None
        return ad

    def __addAttributeGroupDefinition (self, agd):
        local_name = agd.name()
        assert self.__targetNamespace
        tns = self.targetNamespace()
        old_agd = tns.attributeGroupDefinitions().get(local_name)
        if (old_agd is not None) and (old_agd != agd):
            if not old_agd._allowUpdateFromOther(agd):
                raise pyxb.SchemaValidationError('Attempt to re-define non-builtin attribute group definition %s' % (tns.createExpandedName(local_name),))

            # Copy schema-related information from the new definition
            # into the old one, and continue to use the old one.
            tns._replaceComponent(agd, old_agd._updateFromOther(agd))
        else:
            tns.addCategoryObject('attributeGroupDefinition', agd.name(), agd)
        assert agd is not None
        return agd

    def __str__ (self):
        return 'SCH[%s]' % (self.location(),)


def _AddSimpleTypes (namespace):
    """Add to the schema the definitions of the built-in types of XMLSchema.
    This should only be invoked by L{pyxb.namespace} when the built-in
    namespaces are initialized. """
    # Add the ur type
    #schema = namespace.schema()
    schema = Schema(namespace_context=pyxb.namespace.XMLSchema.initialNamespaceContext(), schema_location='URN:noLocation:PyXB:XMLSchema', generation_uid=pyxb.namespace.BuiltInObjectUID, _bypass_preload=True)
    td = schema._addNamedComponent(ComplexTypeDefinition.UrTypeDefinition(schema, in_builtin_definition=True))
    assert td.isResolved()
    # Add the simple ur type
    td = schema._addNamedComponent(SimpleTypeDefinition.SimpleUrTypeDefinition(schema, in_builtin_definition=True))
    assert td.isResolved()
    # Add definitions for all primitive and derived simple types
    pts_std_map = {}
    for dtc in datatypes._PrimitiveDatatypes:
        name = dtc.__name__.rstrip('_')
        td = schema._addNamedComponent(SimpleTypeDefinition.CreatePrimitiveInstance(name, schema, dtc))
        assert td.isResolved()
        assert dtc.SimpleTypeDefinition() == td
        pts_std_map.setdefault(dtc, td)
    for dtc in datatypes._DerivedDatatypes:
        name = dtc.__name__.rstrip('_')
        parent_std = pts_std_map[dtc.XsdSuperType()]
        td = schema._addNamedComponent(SimpleTypeDefinition.CreateDerivedInstance(name, schema, parent_std, dtc))
        assert td.isResolved()
        assert dtc.SimpleTypeDefinition() == td
        pts_std_map.setdefault(dtc, td)
    for dtc in datatypes._ListDatatypes:
        list_name = dtc.__name__.rstrip('_')
        element_name = dtc._ItemType.__name__.rstrip('_')
        element_std = schema.targetNamespace().typeDefinitions().get(element_name)
        assert element_std is not None
        td = schema._addNamedComponent(SimpleTypeDefinition.CreateListInstance(list_name, schema, element_std, dtc))
        assert td.isResolved()
    global _PastAddBuiltInTypes
    _PastAddBuiltInTypes = True

    return schema

import sys
import pyxb.namespace.builtin
pyxb.namespace.builtin._InitializeBuiltinNamespaces(sys.modules[__name__])

## Local Variables:
## fill-column:78
## End:
