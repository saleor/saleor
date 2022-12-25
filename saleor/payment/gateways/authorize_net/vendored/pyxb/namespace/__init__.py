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

"""Classes and global objects related to U{XML Namespaces<http://www.w3.org/TR/2006/REC-xml-names-20060816/index.html>}.

Since namespaces hold all referenceable objects, this module also defines the
infrastructure for resolving named object references, such as schema
components.
"""

import pyxb
import pyxb.utils.utility
from pyxb.utils import six
import xml.dom
import logging

_log = logging.getLogger(__name__)

@pyxb.utils.utility.BackfillComparisons
class ExpandedName (pyxb.cscRoot):

    """Represent an U{expanded name
    <http://www.w3.org/TR/REC-xml-names/#dt-expname>}, which pairs a
    namespace with a local name.

    Because a large number of local elements, and most attributes, have no
    namespace associated with them, this is optimized for representing names
    with an absent namespace.  The hash and equality test methods are set so
    that a plain string is equivalent to a tuple of C{None} and that string.

    Note that absent namespaces can be represented in two ways: with a
    namespace of C{None} (the name "has no namespace"), and with a namespace
    that is an L{absent namespace <Namespace.CreateAbsentNamespace>} (the name
    "has an absent namespace").  Hash code calculations are done so that the
    two alternatives produce the same hash; however, comparison is done so
    that the two are distinguished.  The latter is the intended behavior; the
    former should not be counted upon.

    This class allows direct lookup of the named object within a category by
    using the category name as an accessor function.  That is, if the
    namespace of the expanded name C{en} has a category 'typeDefinition', then
    the following two expressions are equivalent::

      en.typeDefinition()
      en.namespace().categoryMap('typeDefinition').get(en.localName())

    This class descends from C{tuple} so that its values can be used as
    dictionary keys without concern for pointer equivalence.
    """
    def namespace (self):
        """The L{Namespace} part of the expanded name."""
        return self.__namespace
    __namespace = None

    def namespaceURI (self):
        """Return the URI of the namespace, or C{None} if the namespace is absent."""
        return self.__namespaceURI
    __namespaceURI = None

    def localName (self):
        """The local part of the expanded name."""
        return self.__localName
    __localName = None

    # Cached tuple representation
    __expandedName = None

    def validateComponentModel (self):
        """Pass model validation through to namespace part."""
        return self.namespace().validateComponentModel()

    def uriTuple (self):
        """Return a tuple consisting of the namespace URI and the local name.

        This presents the expanded name as base Python types for persistent
        storage.  Be aware, though, that it will lose the association of the
        name with an absent namespace, if that matters to you."""
        return ( self.__namespaceURI, self.__localName )

    # Treat unrecognized attributes as potential accessor functions
    def __getattr__ (self, name):
        # Don't try to recognize private names (like __setstate__)
        if name.startswith('__'):
            return super(ExpandedName, self).__getattr__(name)
        ns = self.namespace()
        if ns is None:
            return lambda: None
        # Anything we're going to look stuff up in requires a component model.
        # Make sure we have one loaded.
        ns.validateComponentModel()
        # NOTE: This will raise pyxb.NamespaceError if the category does not exist.
        category_value = ns.categoryMap(name).get(self.localName())
        return lambda : category_value

    def createName (self, local_name):
        """Return a new expanded name in the namespace of this name.

        @param local_name: The local name portion of an expanded name.
        @return: An instance of L{ExpandedName}.
        """
        return ExpandedName(self.namespace(), local_name)

    def adoptName (self, name):
        """Return the input name, except if the input name has no namespace,
        return a name that uses the namespace from this name with the local
        name from the input name.

        Use this when the XML document has an unqualified name and we're
        processing using an absent default namespace.

        @warning: Be careful when using a global name to adopt a name from a
        local element: if the local element (with no namespace) has the same
        localName as but is different from the global element (with a
        namespace), this will improperly provide a namespace when one should
        not be present.  See the comments in
        L{pyxb.binding.basis.element.elementForName}.
        """

        if not isinstance(name, ExpandedName):
            name = ExpandedName(name)
        if name.namespace() is None:
            name = self.createName(name.localName())
        return name

    def __init__ (self, *args, **kw):
        """Create an expanded name.

        Expected argument patterns are:

         - ( C{str} ) : the local name in an absent namespace
         - ( L{ExpandedName} ) : a copy of the given expanded name
         - ( C{xml.dom.Node} ) : The name extracted from node.namespaceURI and node.localName
         - ( C{str}, C{str} ) : the namespace URI and the local name
         - ( L{Namespace}, C{str} ) : the namespace and the local name
         - ( L{ExpandedName}, C{str}) : the namespace from the expanded name, and the local name

        Wherever C{str} occurs C{unicode} is also permitted.

        @keyword fallback_namespace: Optional Namespace instance to use if the
        namespace would otherwise be None.  This is only used if it is an
        absent namespace.

        """
        fallback_namespace = kw.get('fallback_namespace')
        if 0 == len(args):
            raise pyxb.LogicError('Too few arguments to ExpandedName constructor')
        if 2 < len(args):
            raise pyxb.LogicError('Too many arguments to ExpandedName constructor')
        if 2 == len(args):
            # Namespace(str, unicode, Namespace) and local name basestring
            ( ns, ln ) = args
        else:
            # Local name basestring or ExpandedName or Node
            assert 1 == len(args)
            ln = args[0]
            ns = None
            if isinstance(ln, six.string_types):
                pass
            elif isinstance(ln, tuple) and (2 == len(ln)):
                (ns, ln) = ln
            elif isinstance(ln, ExpandedName):
                ns = ln.namespace()
                ln = ln.localName()
            elif isinstance(ln, xml.dom.Node):
                if not(ln.nodeType in (xml.dom.Node.ELEMENT_NODE, xml.dom.Node.ATTRIBUTE_NODE)):
                    raise pyxb.LogicError('Cannot create expanded name from non-element DOM node %s' % (ln.nodeType,))
                ns = ln.namespaceURI
                ln = ln.localName
            else:
                raise pyxb.LogicError('Unrecognized argument type %s' % (type(ln),))
        if (ns is None) and (fallback_namespace is not None):
            if fallback_namespace.isAbsentNamespace():
                ns = fallback_namespace
        if isinstance(ns, six.string_types):
            ns = NamespaceForURI(ns, create_if_missing=True)
        if isinstance(ns, ExpandedName):
            ns = ns.namespace()
        if (ns is not None) and not isinstance(ns, Namespace):
            raise pyxb.LogicError('ExpandedName must include a valid (perhaps absent) namespace, or None.')
        self.__namespace = ns
        if self.__namespace is not None:
            self.__namespaceURI = self.__namespace.uri()
        self.__localName = ln
        assert self.__localName is not None
        self.__expandedName = ( self.__namespace, self.__localName )
        self.__uriTuple = ( self.__namespaceURI, self.__localName )
        super(ExpandedName, self).__init__(*args, **kw)

    def __str__ (self):
        assert self.__localName is not None
        if self.__namespaceURI is not None:
            return '{%s}%s' % (self.__namespaceURI, self.__localName)
        return self.localName()

    def __hash__ (self):
        if self.__namespaceURI is None:
            # Handle both str and unicode hashes
            return type(self.__localName).__hash__(self.__localName)
        return tuple.__hash__(self.__expandedName)

    def __otherForCompare (self, other):
        if isinstance(other, six.string_types):
            other = ( None, other )
        if not isinstance(other, tuple):
            other = other.__uriTuple
        if isinstance(other[0], Namespace):
            other = ( other[0].uri(), other[1] )
        return other

    def __eq__ (self, other):
        if other is None:
            return False
        return 0 == pyxb.utils.utility.IteratedCompareMixed(self.__uriTuple, self.__otherForCompare(other))

    def __lt__ (self, other):
        if other is None:
            return False
        return 0 > pyxb.utils.utility.IteratedCompareMixed(self.__uriTuple, self.__otherForCompare(other))

    def getAttribute (self, dom_node):
        """Return the value of the attribute identified by this name in the given node.

        @return: An instance of C{xml.dom.Attr}, or C{None} if the node does
        not have an attribute with this name.
        """
        if dom_node.hasAttributeNS(self.__namespaceURI, self.__localName):
            return dom_node.getAttributeNS(self.__namespaceURI, self.__localName)
        return None

    def nodeMatches (self, dom_node):
        """Return C{True} iff the dom node expanded name matches this expanded name."""
        return (dom_node.localName == self.__localName) and (dom_node.namespaceURI == self.__namespaceURI)

class NamedObjectMap (dict):
    """An extended dictionary intended to assist with QName resolution.

    These dictionaries have an attribute that identifies a category of named
    objects within a Namespace; the specifications for various documents
    require that certain groups of objects must be unique, while uniqueness is
    not required between groups.  The dictionary also retains a pointer to the
    Namespace instance for which it holds objects."""
    def namespace (self):
        """The namespace to which the object map belongs."""
        return self.__namespace
    __namespace = None

    def category (self):
        """The category of objects (e.g., typeDefinition, elementDeclaration)."""
        return self.__category
    __category = None

    def __init__ (self, category, namespace, *args, **kw):
        self.__category = category
        self.__namespace = namespace
        super(NamedObjectMap, self).__init__(*args, **kw)

class _NamespaceCategory_mixin (pyxb.cscRoot):
    """Mix-in that aggregates those aspects of XMLNamespaces that hold
    references to categories of named objects.

    Arbitrary groups of named objects, each requiring unique names within
    themselves, can be saved.  Unless configured otherwise, the Namespace
    instance is extended with accessors that provide direct access to
    individual category maps.  The name of the method is the category name
    with a suffix of "s"; e.g., if a category "typeDefinition" exists, it can
    be accessed from the namespace using the syntax C{ns.typeDefinitions()}.

    Note that the returned value from the accessor is a live reference to
    the category map; changes made to the map are reflected in the
    namespace.
    """

    # Map from category strings to NamedObjectMap instances that
    # contain the dictionary for that category.
    __categoryMap = None

    def _reset (self):
        """CSC extension to reset fields of a Namespace.

        This one handles category-related data."""
        getattr(super(_NamespaceCategory_mixin, self), '_reset', lambda *args, **kw: None)()
        self.__categoryMap = { }

    def categories (self):
        """The list of individual categories held in this namespace."""
        return list(self.__categoryMap.keys())

    def _categoryMap (self):
        """Return the whole map from categories to named objects."""
        return self.__categoryMap

    def categoryMap (self, category):
        """Map from local names to NamedObjectMap instances for the given category."""
        try:
            return self.__categoryMap[category]
        except KeyError:
            raise pyxb.NamespaceError(self, '%s has no category %s' % (self, category))

    def __defineCategoryAccessors (self):
        """Define public methods on the Namespace which provide access to
        individual NamedObjectMaps based on their category.

        """
        for category in self.categories():
            accessor_name = category + 's'
            setattr(self, accessor_name, lambda _map=self.categoryMap(category): _map)

    def configureCategories (self, categories):
        """Ensure there is a map for each of the given categories.

        Category configuration
        L{activates<archive._NamespaceArchivable_mixin.isActive>} a namespace.

        Existing maps are not affected."""

        self._activate()
        if self.__categoryMap is None:
            self.__categoryMap = { }
        for category in categories:
            if not (category in self.__categoryMap):
                self.__categoryMap[category] = NamedObjectMap(category, self)
        self.__defineCategoryAccessors()
        return self

    def addCategoryObject (self, category, local_name, named_object):
        """Allow access to the named_object by looking up the local_name in
        the given category.

        Raises pyxb.NamespaceUniquenessError if an object with the same name
        already exists in the category."""
        name_map = self.categoryMap(category)
        old_object = name_map.get(local_name)
        if (old_object is not None) and (old_object != named_object):
            raise pyxb.NamespaceUniquenessError(self, '%s: name %s used for multiple values in %s' % (self, local_name, category))
        name_map[local_name] = named_object
        return named_object

    def replaceCategoryObject (self, category, local_name, old_object, new_object):
        """Replace the referenced object in the category.

        The new object will be added only if the old_object matches the
        current entry for local_name in the category."""
        name_map = self.categoryMap(category)
        if old_object == name_map.get(local_name):
            name_map[local_name] = new_object
        return name_map[local_name]

    def _replaceComponent_csc (self, existing_def, replacement_def):
        """Replace a component definition where present in the category maps.

        @note: This is a high-cost operation, as every item in every category
        map must be examined to see whether its value field matches
        C{existing_def}."""
        for (cat, registry) in six.iteritems(self.__categoryMap):
            for (k, v) in registry.items(): # NB: Not iteritems
                if v == existing_def:
                    del registry[k]
                    if replacement_def is not None:
                        registry[k] = replacement_def
        return getattr(super(_NamespaceCategory_mixin, self), '_replaceComponent_csc', lambda *args, **kw: replacement_def)(existing_def, replacement_def)

    # Verify that the namespace category map has no components recorded.  This
    # is the state that should hold prior to loading a saved namespace; at
    # tthe moment, we do not support aggregating components defined separately
    # into the same namespace.  That should be done at the schema level using
    # the "include" element.
    def __checkCategoriesEmpty (self):
        if self.__categoryMap is None:
            return True
        assert isinstance(self.__categoryMap, dict)
        if 0 == len(self.__categoryMap):
            return True
        for k in self.categories():
            if 0 < len(self.categoryMap(k)):
                return False
        return True

    def _namedObjects (self):
        objects = set()
        for category_map in six.itervalues(self.__categoryMap):
            objects.update(six.itervalues(category_map))
        return objects

    def _loadNamedObjects (self, category_map):
        """Add the named objects from the given map into the set held by this namespace.
        It is an error to name something which is already present."""
        self.configureCategories(six.iterkeys(category_map))
        for category in six.iterkeys(category_map):
            current_map = self.categoryMap(category)
            new_map = category_map[category]
            for (local_name, component) in six.iteritems(new_map):
                existing_component = current_map.get(local_name)
                if existing_component is None:
                    current_map[local_name] = component
                elif existing_component._allowUpdateFromOther(component):
                    existing_component._updateFromOther(component)
                else:
                    raise pyxb.NamespaceError(self, 'Load attempted to override %s %s in %s' % (category, local_name, self.uri()))
        self.__defineCategoryAccessors()

    def hasSchemaComponents (self):
        """Return C{True} iff schema components have been associated with this namespace.

        This only checks whether the corresponding categories have been added,
        not whether there are any entries in those categories.  It is useful
        for identifying namespaces that were incorporated through a
        declaration but never actually referenced."""
        return 'typeDefinition' in self.__categoryMap

    def _associateOrigins (self, module_record):
        """Add links from L{pyxb.namespace.archive._ObjectOrigin} instances.

        For any resolvable item in this namespace from an origin managed by
        the module_record, ensure that item can be found via a lookup through
        that origin.

        This allows these items to be found when a single namespace comprises
        items translated from different schema at different times using
        archives to maintain consistency."""
        assert module_record.namespace() == self
        module_record.resetCategoryObjects()
        self.configureCategories([archive.NamespaceArchive._AnonymousCategory()])
        origin_set = module_record.origins()
        for (cat, cat_map) in six.iteritems(self.__categoryMap):
            for (n, v) in six.iteritems(cat_map):
                if isinstance(v, archive._ArchivableObject_mixin) and (v._objectOrigin() in origin_set):
                    v._objectOrigin().addCategoryMember(cat, n, v)

class _ComponentDependency_mixin (pyxb.utils.utility.PrivateTransient_mixin, pyxb.cscRoot):
    """Mix-in for components that can depend on other components."""

    __PrivateTransient = set()

    # Cached frozenset of components on which this component depends.
    __bindingRequires = None
    __PrivateTransient.add('bindingRequires')

    def _resetClone_csc (self, **kw):
        """CSC extension to reset fields of a component.  This one clears
        dependency-related data, since the clone will have to revise its
        dependencies.
        @rtype: C{None}"""
        getattr(super(_ComponentDependency_mixin, self), '_resetClone_csc', lambda *_args, **_kw: None)(**kw)
        self.__bindingRequires = None

    def bindingRequires (self, reset=False, include_lax=False):
        """Return a set of components upon whose bindings this component's
        bindings depend.

        For example, bindings that are extensions or restrictions depend on
        their base types.  Complex type definition bindings require that the
        types of their attribute declarations be available at the class
        definition, and the types of their element declarations in the
        postscript.

        @keyword include_lax: if C{False} (default), only the requirements of
        the class itself are returned.  If C{True}, all requirements are
        returned.
        @rtype: C{set(L{pyxb.xmlschema.structures._SchemaComponent_mixin})}
        """
        if reset or (self.__bindingRequires is None):
            if isinstance(self, resolution._Resolvable_mixin) and not (self.isResolved()):
                raise pyxb.LogicError('Unresolved %s in %s: %s' % (self.__class__.__name__, self._namespaceContext().targetNamespace(), self.name()))
            self.__bindingRequires = self._bindingRequires_vx(include_lax)
        return self.__bindingRequires

    def _bindingRequires_vx (self, include_lax):
        """Placeholder for subclass method that identifies the necessary components.

        @note: Override in subclasses.

        @return: The component instances on which this component depends
        @rtype: C{frozenset}
        @raise LogicError: A subclass failed to implement this method
        """
        raise pyxb.LogicError('%s does not implement _bindingRequires_vx' % (type(self),))

class _NamespaceComponentAssociation_mixin (pyxb.cscRoot):
    """Mix-in for managing components defined within this namespace.

    The component set includes not only top-level named components (such as
    those accessible through category maps), but internal anonymous
    components, such as those involved in representing the content model of a
    complex type definition.  We need to be able to get a list of these
    components, sorted in dependency order, so that generated bindings do not
    attempt to refer to a binding that has not yet been generated."""

    # A set containing all components, named or unnamed, that belong to this
    # namespace.
    __components = None

    def _reset (self):
        """CSC extension to reset fields of a Namespace.

        This one handles data related to component association with a
        namespace."""
        getattr(super(_NamespaceComponentAssociation_mixin, self), '_reset', lambda *args, **kw: None)()
        self.__components = set()
        self.__origins = set()
        self.__schemaMap = { }

    def _associateComponent (self, component):
        """Record that the responsibility for the component belongs to this namespace."""
        self._activate()
        assert self.__components is not None
        assert isinstance(component, _ComponentDependency_mixin)
        assert component not in self.__components
        self.__components.add(component)

    def _replaceComponent_csc (self, existing_def, replacement_def):
        """Replace a component definition in the set of associated components.

        @raise KeyError: C{existing_def} is not in the set of components."""

        self.__components.remove(existing_def)
        if replacement_def is not None:
            self.__components.add(replacement_def)
        return getattr(super(_NamespaceComponentAssociation_mixin, self), '_replaceComponent_csc', lambda *args, **kw: replacement_def)(existing_def, replacement_def)

    def addSchema (self, schema):
        for sr in self.__origins:
            if isinstance(sr, archive._SchemaOrigin) and sr.match(schema=schema):
                _log.info('Hash for %s matches %s already registered as %s', schema.location(), sr.schema().location(), self)
                raise pyxb.SchemaUniquenessError(self, schema.location(), sr.schema())
        sr = archive._SchemaOrigin(schema=schema)
        schema.generationUID().associateObject(sr)
        self.__origins.add(sr)
        return sr

    def lookupSchemaByLocation (self, schema_location):
        for sr in self.__origins:
            if isinstance(sr, archive._SchemaOrigin) and sr.match(location=schema_location):
                return (True, sr.schema())
        for mr in self.moduleRecords():
            if mr.hasMatchingOrigin(location=schema_location):
                return (True, None)
        return (False, None)

    def schemas (self):
        s = set()
        for sr in self.__origins:
            if isinstance(sr, archive._SchemaOrigin) and (sr.schema() is not None):
                s.add(sr.schema())
        return s

    __origins = None

    def components (self):
        """Return a frozenset of all components, named or unnamed, belonging
        to this namespace."""
        return frozenset(self.__components)

    def _releaseNamespaceContexts (self):
        for c in self.__components:
            c._clearNamespaceContext()

from pyxb.namespace import archive
from pyxb.namespace.utility import NamespaceInstance
from pyxb.namespace.utility import NamespaceForURI
from pyxb.namespace.utility import CreateAbsentNamespace
from pyxb.namespace.utility import AvailableNamespaces
from pyxb.namespace import resolution
NamespaceContext = resolution.NamespaceContext

class Namespace (_NamespaceCategory_mixin, resolution._NamespaceResolution_mixin, _NamespaceComponentAssociation_mixin, archive._NamespaceArchivable_mixin):
    """Represents an XML namespace (a URI).

    There is at most one L{Namespace} class instance per namespace (URI).  The
    instance also supports associating arbitrary L{maps<NamedObjectMap>} from
    names to objects, in separate categories.  The default categories are
    configured externally; for example, the
    L{Schema<pyxb.xmlschema.structures.Schema>} component defines a category
    for each named component in XMLSchema, and the customizing subclass for
    WSDL definitions adds categories for the service bindings, messages, etc.

    Namespaces can be written to and loaded from pickled files.  See
    L{NamespaceArchive} for information.
    """

    # The URI for the namespace.  If the URI is None, this is an absent
    # namespace.
    __uri = None

    # An identifier, unique within a program using PyXB, used to distinguish
    # absent namespaces.  Currently this value is not accessible to the user,
    # and exists solely to provide a unique identifier when printing the
    # namespace as a string.  The class variable is used as a one-up counter,
    # which is assigned to the instance variable when an absent namespace
    # instance is created.
    __absentNamespaceID = 0

    # A prefix bound to this namespace by standard.  Current set known are applies to
    # xml and xmlns.
    __boundPrefix = None

    # A prefix set as a preferred prefix, generally by processing a namespace
    # declaration.
    __prefix = None

    # A map from URIs to Namespace instances.  Namespaces instances
    # must be unique for their URI.  See __new__().
    __Registry = { }

    # A set of all absent namespaces created.
    __AbsentNamespaces = set()

    # Optional description of the namespace
    __description = None

    # Indicates whether this namespace is built-in to the system
    __isBuiltinNamespace = False

    # Indicates whether this namespace is undeclared (available always)
    __isUndeclaredNamespace = False

    # Indicates whether this namespace was loaded from an archive
    __isLoadedNamespace = False

    # Archive from which the namespace can be read, or None if no archive
    # defines this namespace.
    __namespaceArchive = None

    # Indicates whether this namespace has been written to an archive
    __hasBeenArchived = False

    # Holds the module path for builtin modules until we get a ModuleRecord to
    # store that in.
    __builtinModulePath = None

    # A set of options defining how the Python bindings for this namespace
    # were generated.  Not currently used, since we don't have different
    # binding configurations yet.
    __bindingConfiguration = None

    # The namespace to use as the default namespace when constructing the
    # The namespace context used when creating built-in components that belong
    # to this namespace.  This is used to satisfy the low-level requirement
    # that all schema components have a namespace context; normally, that
    # context is built dynamically from the schema element.
    __initialNamespaceContext = None

    # The default_namespace parameter when creating the initial namespace
    # context.  Only used with built-in namespaces.
    __contextDefaultNamespace = None

    # The map from prefixes to namespaces as defined by the schema element for
    # this namespace.  Only used with built-in namespaces.
    __contextInScopeNamespaces = None

    @classmethod
    def _NamespaceForURI (cls, uri):
        """If a Namespace instance for the given URI exists, return it; otherwise return None.

        Note: Absent namespaces are not stored in the registry.  If you use
        one (e.g., for a schema with no target namespace), don't lose hold of
        it."""
        if uri is None:
            raise pyxb.UsageError('Absent namespaces are unlocatable')
        return cls.__Registry.get(uri)

    # A map from string UUIDs to absent Namespace instances.  Used for
    # in-session deserialization as required for cloning objects.  Non-absent
    # namespaces are identified by URI and recorded in __Registry.
    __AbsentNamespaceRegistry = { }

    # The UUID used to serialize this namespace. This serves the same role in
    # __AbsentNamespaceRegistry as the namespace URI does in __Registry, but
    # is retained only within a single PyXB session.
    __absentSerializedUUID = None

    __SerializedVariantAbsent = 'absent'

    def __getnewargs__ (self):
        """Pickling support.

        To ensure that unpickled Namespace instances are unique per
        URI, we ensure that the routine that creates unpickled
        instances knows what it's supposed to return."""
        if self.uri() is None:
            # We can't reconstruct absent namespaces.  However, it is
            # convenient to be able to use Python's copy module to clone
            # instances.  Support for that does require ability to identify
            # specific absent namespaces, which we do by representing them as
            # a tuple containing a variant tag and unique identifier.
            if self.__absentSerializedUUID is None:
                _log.warning('Instances with absent namespaces can only be reconstructed in-session')
                self.__absentSerializedUUID = pyxb.utils.utility.UniqueIdentifier()
                self.__AbsentNamespaceRegistry[self.__absentSerializedUUID.uid()] = self
            return ((self.__SerializedVariantAbsent, self.__absentSerializedUUID.uid()),)
        return (self.uri(),)

    def __new__ (cls, *args, **kw):
        """Pickling and singleton support.

        This ensures that no more than one Namespace instance exists
        for any given URI.  We could do this up in __init__, but that
        doesn't normally get called when unpickling instances; this
        does.  See also __getnewargs__()."""
        (uri,) = args
        if isinstance(uri, tuple):
            # Special handling to reconstruct absent namespaces.
            (variant, uid) = uri
            if cls.__SerializedVariantAbsent == variant:
                ns = cls.__AbsentNamespaceRegistry.get(uid)
                if ns is None:
                    raise pyxb.UsageError('Unable to reconstruct instance of absent namespace')
                return ns
            raise pyxb.LogicError('Unrecognized serialized namespace variant %s uid %s' % (variant, uid))
        elif not (uri in cls.__Registry):
            instance = object.__new__(cls)
            # Do this one step of __init__ so we can do checks during unpickling
            instance.__uri = uri
            instance._reset()
            # Absent namespaces are not stored in the registry.
            if uri is None:
                cls.__AbsentNamespaces.add(instance)
                return instance
            cls.__Registry[uri] = instance
        return cls.__Registry[uri]

    @classmethod
    def AvailableNamespaces (cls):
        """Return a set of all Namespace instances defined so far."""
        return cls.__AbsentNamespaces.union(six.itervalues(cls.__Registry))

    def __init__ (self, uri,
                  description=None,
                  builtin_namespace=None,
                  builtin_module_path=None,
                  is_undeclared_namespace=False,
                  is_loaded_namespace=False,
                  bound_prefix=None,
                  default_namespace=None,
                  in_scope_namespaces=None):
        """Create a new Namespace.

        The URI must be non-None, and must not already be assigned to
        a Namespace instance.  See _NamespaceForURI().

        User-created Namespace instances may also provide a description.

        Users should never provide a builtin_namespace parameter.
        """

        # New-style superclass invocation
        super(Namespace, self).__init__()

        self.__contextDefaultNamespace = default_namespace
        self.__contextInScopeNamespaces = in_scope_namespaces

        # Make sure that we're not trying to do something restricted to
        # built-in namespaces
        is_builtin_namespace = not (builtin_namespace is None)
        if not is_builtin_namespace:
            if bound_prefix is not None:
                raise pyxb.LogicError('Only permanent Namespaces may have bound prefixes')

        # We actually set the uri when this instance was allocated;
        # see __new__().
        assert self.__uri == uri
        self.__boundPrefix = bound_prefix
        self.__description = description
        self.__isBuiltinNamespace = is_builtin_namespace
        self.__builtinNamespaceVariable = builtin_namespace
        self.__builtinModulePath = builtin_module_path
        self.__isUndeclaredNamespace = is_undeclared_namespace
        self.__isLoadedNamespace = is_loaded_namespace

        self._reset()

        assert (self.__uri is None) or (self.__Registry[self.__uri] == self)

    def _reset (self):
        assert not self.isActive()
        getattr(super(Namespace, self), '_reset', lambda *args, **kw: None)()
        self.__initialNamespaceContext = None

    def uri (self):
        """Return the URI for the namespace represented by this instance.

        If the URI is None, this is an absent namespace, used to hold
        declarations not associated with a namespace (e.g., from schema with
        no target namespace)."""
        return self.__uri

    def setPrefix (self, prefix):
        if self.__boundPrefix is not None:
            if self.__boundPrefix == prefix:
                return self
            raise pyxb.NamespaceError(self, 'Cannot change the prefix of a bound namespace')
        self.__prefix = prefix
        return self

    def prefix (self):
        if self.__boundPrefix:
            return self.__boundPrefix
        return self.__prefix

    def isAbsentNamespace (self):
        """Return True iff this namespace is an absent namespace.

        Absent namespaces have no namespace URI; they exist only to
        hold components created from schemas with no target
        namespace."""
        return self.__uri is None

    def fallbackNamespace (self):
        """When known to be operating in this namespace, provide the Namespace
        instance to be used when names are associated with no namespace."""
        if self.isAbsentNamespace():
            return self
        return None

    @classmethod
    def CreateAbsentNamespace (cls):
        """Create an absent namespace.

        Use this instead of the standard constructor, in case we need
        to augment it with a uuid or the like."""
        rv = Namespace(None)
        rv.__absentNamespaceID = cls.__absentNamespaceID
        cls.__absentNamespaceID += 1

        return rv

    def _overrideAbsentNamespace (self, uri):
        assert self.isAbsentNamespace()
        self.__uri = uri

    def boundPrefix (self):
        """Return the standard prefix to be used for this namespace.

        Only a few namespace prefixes are bound to namespaces: xml and xmlns
        are two.  In all other cases, this method should return None.  The
        infrastructure attempts to prevent user creation of Namespace
        instances that have bound prefixes."""
        return self.__boundPrefix

    def isBuiltinNamespace (self):
        """Return True iff this namespace was defined by the infrastructure.

        That is the case for all namespaces in the Namespace module."""
        return self.__isBuiltinNamespace

    def builtinNamespaceRepresentation (self):
        assert self.__builtinNamespaceVariable is not None
        return 'pyxb.namespace.%s' % (self.__builtinNamespaceVariable,)

    def builtinModulePath (self):
        from pyxb.namespace import builtin
        if not self.__builtinModulePath:
            raise pyxb.LogicError('Namespace has no built-in module: %s' % (self,))
        mr = self.lookupModuleRecordByUID(builtin.BuiltInObjectUID)
        assert mr is not None
        assert mr.modulePath() == self.__builtinModulePath
        return self.__builtinModulePath

    def isUndeclaredNamespace (self):
        """Return True iff this namespace is always available
        regardless of whether there is a declaration for it.

        This is the case only for the
        xml(http://www.w3.org/XML/1998/namespace) and
        xmlns(http://www.w3.org/2000/xmlns/) namespaces."""
        return self.__isUndeclaredNamespace

    def isLoadedNamespace (self):
        """Return C{True} iff this namespace was loaded from a namespace archive."""
        return self.__isLoadedNamespace

    def hasBeenArchived (self):
        """Return C{True} iff this namespace has been saved to a namespace archive.
        See also L{isLoadedNamespace}."""
        return self.__hasBeenArchived

    def description (self, description=None):
        """Get, or set, a textual description of the namespace."""
        if description is not None:
            self.__description = description
        return self.__description

    def nodeIsNamed (self, node, *local_names):
        return (node.namespaceURI == self.uri()) and (node.localName in local_names)

    def createExpandedName (self, local_name):
        return ExpandedName(self, local_name)

    def __getstate__ (self):
        """Support pickling.

        Well, no, not really.  Because namespace instances must be unique, we
        represent them as their URI, and that's done by __getnewargs__
        above.  All the interesting information is in the ModuleRecords."""
        return {}

    def _defineBuiltins_ox (self, structures_module):
        pass

    __definedBuiltins = False
    def _defineBuiltins (self, structures_module):
        assert self.isBuiltinNamespace()
        if not self.__definedBuiltins:
            from pyxb.namespace import builtin
            mr = self.lookupModuleRecordByUID(builtin.BuiltInObjectUID, create_if_missing=True, module_path=self.__builtinModulePath)
            self._defineBuiltins_ox(structures_module)
            self.__definedBuiltins = True
            mr.markIncorporated()
        return self

    def _loadComponentsFromArchives (self, structures_module):
        """Attempts to load the named objects held in this namespace.

        The base class implementation looks at the set of available archived
        namespaces, and if one contains this namespace unserializes its named
        object maps.

        Sub-classes may choose to look elsewhere, if this version fails or
        before attempting it.

        There is no guarantee that any particular category of named object has
        been located when this returns.  Caller must check.
        """
        for mr in self.moduleRecords():
            if mr.isLoadable():
                if mr.isPublic():
                    _log.info('Load %s from %s', mr, mr.archive())
                    try:
                        mr.archive().readNamespaces()
                    except pyxb.NamespaceArchiveError:
                        _log.exception("Failure reading namespaces in archive")
                else:
                    _log.info('Ignoring private module %s in validation', mr)
        self._activate()

    __didValidation = False
    __inValidation = False
    def validateComponentModel (self, structures_module=None):
        """Ensure this namespace is ready for use.

        If the namespace does not have a map of named objects, the system will
        attempt to load one.
        """
        if not self.__didValidation:
            # assert not self.__inValidation, 'Nested validation of %s' % (self.uri(),)
            if structures_module is None:
                import pyxb.xmlschema.structures as structures_module
            if self.isBuiltinNamespace():
                self._defineBuiltins(structures_module)
            try:
                self.__inValidation = True
                self._loadComponentsFromArchives(structures_module)
                self.__didValidation = True
            finally:
                self.__inValidation = False
        return True

    def _replaceComponent (self, existing_def, replacement_def):
        """Replace the existing definition with another.

        This is used in a situation where building the component model
        resulted in a new component instance being created and registered, but
        for which an existing component is to be preferred.  An example is
        when parsing the schema for XMLSchema itself: the built-in datatype
        components should be retained instead of the simple type definition
        components dynamically created from the schema.

        By providing the value C{None} as the replacement definition, this can
        also be used to remove components.

        @note: Invoking this requires scans of every item in every category
        map in the namespace.

        @return: C{replacement_def}
        """
        # We need to do replacements in the category map handler, the
        # resolver, and the component associator.
        return self._replaceComponent_csc(existing_def, replacement_def)

    def initialNamespaceContext (self):
        """Obtain the namespace context to be used when creating components in this namespace.

        Usually applies only to built-in namespaces, but is also used in the
        autotests when creating a namespace without a xs:schema element.  .
        Note that we must create the instance dynamically, since the
        information that goes into it has cross-dependencies that can't be
        resolved until this module has been completely loaded."""

        if self.__initialNamespaceContext is None:
            isn = { }
            if self.__contextInScopeNamespaces is not None:
                for (k, v) in six.iteritems(self.__contextInScopeNamespaces):
                    isn[k] = self.__identifyNamespace(v)
            kw = { 'target_namespace' : self
                 , 'default_namespace' : self.__identifyNamespace(self.__contextDefaultNamespace)
                 , 'in_scope_namespaces' : isn }
            self.__initialNamespaceContext = resolution.NamespaceContext(None, **kw)
        return self.__initialNamespaceContext


    def __identifyNamespace (self, nsval):
        """Identify the specified namespace, which should be a built-in.

        Normally we can just use a reference to the Namespace module instance,
        but when creating those instances we sometimes need to refer to ones
        for which the instance has not yet been created.  In that case, we use
        the name of the instance, and resolve the namespace when we need to
        create the initial context."""
        if nsval is None:
            return self
        if isinstance(nsval, six.string_types):
            nsval = globals().get(nsval)
        if isinstance(nsval, Namespace):
            return nsval
        raise pyxb.LogicError('Cannot identify namespace from %s' % (nsval,))

    def __str__ (self):
        if self.__uri is None:
            return 'AbsentNamespace%d' % (self.__absentNamespaceID,)
        assert self.__uri is not None
        if self.__boundPrefix is not None:
            rv = '%s=%s' % (self.__boundPrefix, self.__uri)
        else:
            rv = self.__uri
        return rv

from pyxb.namespace.builtin import XMLSchema_instance
from pyxb.namespace.builtin import XMLNamespaces
from pyxb.namespace.builtin import XMLSchema
from pyxb.namespace.builtin import XHTML
from pyxb.namespace.builtin import XML
from pyxb.namespace.builtin import XMLSchema_hfp
from pyxb.namespace.builtin import BuiltInObjectUID

resolution.NamespaceContext._AddTargetNamespaceAttribute(XMLSchema.createExpandedName('schema'), ExpandedName('targetNamespace'))

## Local Variables:
## fill-column:78
## End:
