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

"""Classes and global objects related to resolving U{XML
Namespaces<http://www.w3.org/TR/2006/REC-xml-names-20060816/index.html>}."""

import logging
import pyxb
import pyxb.utils.utility
from pyxb.namespace import archive, utility
from pyxb.utils import six

_log = logging.getLogger(__name__)

class _Resolvable_mixin (pyxb.cscRoot):
    """Mix-in indicating that this object may have references to unseen named components.

    This class is mixed-in to those XMLSchema components that have a reference
    to another component that is identified by a QName.  Resolution of that
    component may need to be delayed if the definition of the component has
    not yet been read.
    """

    #_TraceResolution = True
    _TraceResolution = False

    def isResolved (self):
        """Determine whether this named component is resolved.

        Override this in the child class."""
        raise NotImplementedError("_Resolvable_mixin.isResolved in %s"% (type(self).__name__,))

    def _resolve (self):
        """Perform whatever steps are required to resolve this component.

        Resolution is performed in the context of the namespace to which the
        component belongs.  Invoking this method may fail to complete the
        resolution process if the component itself depends on unresolved
        components.  The sole caller of this should be
        L{_NamespaceResolution_mixin.resolveDefinitions}.

        This method is permitted (nay, encouraged) to raise an exception if
        resolution requires interpreting a QName and the named component
        cannot be found.

        Override this in the child class.  In the prefix, if L{isResolved} is
        true, return right away.  If something prevents you from completing
        resolution, invoke L{self._queueForResolution()} (so it is retried
        later) and immediately return self.  Prior to leaving after successful
        resolution discard any cached dom node by setting C{self.__domNode=None}.

        @return: C{self}, whether or not resolution succeeds.
        @raise pyxb.SchemaValidationError: if resolution requlres a reference to an unknown component
        """
        raise NotImplementedError("_Resolvable_mixin._resolve in %s"% (type(self).__name__,))

    def _queueForResolution (self, why=None, depends_on=None):
        """Short-hand to requeue an object if the class implements _namespaceContext().
        """
        if (why is not None) and self._TraceResolution:
            _log.info('Resolution delayed for %s: %s\n\tDepends on: %s', self, why, depends_on)
        self._namespaceContext().queueForResolution(self, depends_on)

class _NamespaceResolution_mixin (pyxb.cscRoot):
    """Mix-in that aggregates those aspects of XMLNamespaces relevant to
    resolving component references.
    """

    # A set of namespaces which some schema imported while processing with
    # this namespace as target.
    __importedNamespaces = None

    # A set of namespaces which appear in namespace declarations of schema
    # with this namespace as target.
    __referencedNamespaces = None

    # A list of Namespace._Resolvable_mixin instances that have yet to be
    # resolved.
    __unresolvedComponents = None

    # A map from Namespace._Resolvable_mixin instances in
    # __unresolvedComponents to sets of other unresolved objects on which they
    # depend.
    __unresolvedDependents = None

    def _reset (self):
        """CSC extension to reset fields of a Namespace.

        This one handles component-resolution--related data."""
        getattr(super(_NamespaceResolution_mixin, self), '_reset', lambda *args, **kw: None)()
        self.__unresolvedComponents = []
        self.__unresolvedDependents = {}
        self.__importedNamespaces = set()
        self.__referencedNamespaces = set()

    def _getState_csc (self, kw):
        kw.update({
                'importedNamespaces': self.__importedNamespaces,
                'referencedNamespaces': self.__referencedNamespaces,
                })
        return getattr(super(_NamespaceResolution_mixin, self), '_getState_csc', lambda _kw: _kw)(kw)

    def _setState_csc (self, kw):
        self.__importedNamespaces = kw['importedNamespaces']
        self.__referencedNamespaces = kw['referencedNamespaces']
        return getattr(super(_NamespaceResolution_mixin, self), '_setState_csc', lambda _kw: self)(kw)

    def importNamespace (self, namespace):
        self.__importedNamespaces.add(namespace)
        return self

    def _referenceNamespace (self, namespace):
        self._activate()
        self.__referencedNamespaces.add(namespace)
        return self

    def importedNamespaces (self):
        """Return the set of namespaces which some schema imported while
        processing with this namespace as target."""
        return frozenset(self.__importedNamespaces)

    def _transferReferencedNamespaces (self, module_record):
        assert isinstance(module_record, archive.ModuleRecord)
        module_record._setReferencedNamespaces(self.__referencedNamespaces)
        self.__referencedNamespaces.clear()

    def referencedNamespaces (self):
        """Return the set of namespaces which appear in namespace declarations
        of schema with this namespace as target."""
        return frozenset(self.__referencedNamespaces)

    def queueForResolution (self, resolvable, depends_on=None):
        """Invoked to note that a component may have references that will need
        to be resolved.

        Newly created named components are often unresolved, as are components
        which, in the course of resolution, are found to depend on another
        unresolved component.

        @param resolvable: An instance of L{_Resolvable_mixin} that is later to
        be resolved.

        @keyword depends_on: C{None}, or an instance of L{_Resolvable_mixin}
        which C{resolvable} requires to be resolved in order to resolve
        itself.

        @return: C{resolvable}
        """
        assert isinstance(resolvable, _Resolvable_mixin)
        if not resolvable.isResolved():
            assert depends_on is None or isinstance(depends_on, _Resolvable_mixin)
            self.__unresolvedComponents.append(resolvable)
            if depends_on is not None and not depends_on.isResolved():
                from pyxb.xmlschema import structures
                assert isinstance(depends_on, _Resolvable_mixin)
                assert isinstance(depends_on, structures._NamedComponent_mixin)
                self.__unresolvedDependents.setdefault(resolvable, set()).add(depends_on)
        return resolvable

    def needsResolution (self):
        """Return C{True} iff this namespace has not been resolved."""
        return self.__unresolvedComponents is not None

    def _replaceComponent_csc (self, existing_def, replacement_def):
        """Replace a component definition if present in the list of unresolved components.
        """
        try:
            index = self.__unresolvedComponents.index(existing_def)
            if (replacement_def is None) or (replacement_def in self.__unresolvedComponents):
                del self.__unresolvedComponents[index]
            else:
                assert isinstance(replacement_def, _Resolvable_mixin)
                self.__unresolvedComponents[index] = replacement_def
            # Rather than assume the replacement depends on the same
            # resolvables as the original, just wipe the dependency record:
            # it'll get recomputed later if it's still important.
            if existing_def in self.__unresolvedDependents:
                del self.__unresolvedDependents[existing_def]
        except ValueError:
            pass
        return getattr(super(_NamespaceResolution_mixin, self), '_replaceComponent_csc', lambda *args, **kw: replacement_def)(existing_def, replacement_def)

    def resolveDefinitions (self, allow_unresolved=False):
        """Loop until all references within the associated resolvable objects
        have been resolved.

        This method iterates through all components on the unresolved list,
        invoking the _resolve method of each.  If the component could not be
        resolved in this pass, it iis placed back on the list for the next
        iteration.  If an iteration completes without resolving any of the
        unresolved components, a pyxb.NotInNamespaceError exception is raised.

        @note: Do not invoke this until all top-level definitions for the
        namespace have been provided.  The resolution routines are entitled to
        raise a validation exception if a reference to an unrecognized
        component is encountered.
        """
        if not self.needsResolution():
            return True

        while 0 < len(self.__unresolvedComponents):
            # Save the list of unresolved objects, reset the list to capture
            # any new objects defined during resolution, and attempt the
            # resolution for everything that isn't resolved.
            unresolved = self.__unresolvedComponents

            self.__unresolvedComponents = []
            self.__unresolvedDependents = {}
            for resolvable in unresolved:
                # Attempt the resolution.
                resolvable._resolve()

                # Either we resolved it, or we queued it to try again later
                assert resolvable.isResolved() or (resolvable in self.__unresolvedComponents), 'Lost resolvable %s' % (resolvable,)

                # We only clone things that have scope None.  We never
                # resolve things that have scope None.  Therefore, we
                # should never have resolved something that has
                # clones.
                if (resolvable.isResolved() and (resolvable._clones() is not None)):
                    assert False
            if self.__unresolvedComponents == unresolved:
                if allow_unresolved:
                    return False
                # This only happens if we didn't code things right, or the
                # there is a circular dependency in some named component
                # (i.e., the schema designer didn't do things right).
                failed_components = []
                from pyxb.xmlschema import structures
                for d in self.__unresolvedComponents:
                    if isinstance(d, structures._NamedComponent_mixin):
                        failed_components.append('%s named %s' % (d.__class__.__name__, d.name()))
                    else:
                        failed_components.append('Anonymous %s' % (d.__class__.__name__,))
                raise pyxb.NotInNamespaceError('Infinite loop in resolution:\n  %s' % ("\n  ".join(failed_components),))

        # Replace the list of unresolved components with None, so that
        # attempts to subsequently add another component fail.
        self.__unresolvedComponents = None
        self.__unresolvedDependents = None

        # NOTE: Dependencies may require that we keep these around for a while
        # longer.
        #
        # Remove the namespace context from everything, since we won't be
        # resolving anything else.
        self._releaseNamespaceContexts()

        return True

    def _unresolvedComponents (self):
        """Returns a reference to the list of unresolved components."""
        return self.__unresolvedComponents

    def _unresolvedDependents (self):
        """Returns a map from unresolved components to sets of components that
        must be resolved first."""
        return self.__unresolvedDependents

def ResolveSiblingNamespaces (sibling_namespaces):
    """Resolve all components in the sibling_namespaces.

    @param sibling_namespaces : A set of namespaces expected to be closed
    under dependency."""

    for ns in sibling_namespaces:
        ns.configureCategories([archive.NamespaceArchive._AnonymousCategory()])
        ns.validateComponentModel()

    def __keyForCompare (dependency_map):
        """Sort namespaces so dependencies get resolved first.

        Uses the trick underlying functools.cmp_to_key(), but optimized for
        this special case.  The dependency map is incorporated into the class
        definition by scope.
        """
        class K (object):
            def __init__ (self, ns, *args):
                self.__ns = ns

            # self compares less than other if self.ns is in the dependency set
            # of other.ns but not vice-versa.
            def __lt__ (self, other):
                return ((self.__ns in dependency_map.get(other.__ns, set())) \
                            and not (other.__ns in dependency_map.get(self.__ns, set())))

            # self compares equal to other if their namespaces are either
            # mutually dependent or independent.
            def __eq__ (self, other):
                return (self.__ns in dependency_map.get(other.__ns, set())) == (other.__ns in dependency_map.get(self.__ns, set()))

            # All other order metrics are derived.
            def __ne__ (self, other):
                return not self.__eq__(other)
            def __le__ (self, other):
                return self.__lt__(other) or self.__eq__(other)
            def __gt__ (self, other):
                return other.__lt__(self.__ns)
            def __ge__ (self, other):
                return other.__lt__(self.__ns) or self.__eq__(other)
        return K

    need_resolved_set = set(sibling_namespaces)
    dependency_map = {}
    last_state = None
    while need_resolved_set:
        need_resolved_list = list(need_resolved_set)
        if dependency_map:
            need_resolved_list.sort(key=__keyForCompare(dependency_map))
        need_resolved_set = set()
        dependency_map = {}
        for ns in need_resolved_list:
            if not ns.needsResolution():
                continue
            if not ns.resolveDefinitions(allow_unresolved=True):
                deps = dependency_map.setdefault(ns, set())
                for (c, dcs) in six.iteritems(ns._unresolvedDependents()):
                    for dc in dcs:
                        dns = dc.expandedName().namespace()
                        if dns != ns:
                            deps.add(dns)
                _log.info('Holding incomplete resolution %s depending on: ', ns.uri(), six.u(' ; ').join([ six.text_type(_dns) for _dns in deps ]))
                need_resolved_set.add(ns)
        # Exception termination check: if we have the same set of incompletely
        # resolved namespaces, and each has the same number of unresolved
        # components, assume there's an truly unresolvable dependency: either
        # due to circularity, or because there was an external namespace that
        # was missed from the sibling list.
        state = []
        for ns in need_resolved_set:
            state.append( (ns, len(ns._unresolvedComponents())) )
        state = tuple(state)
        if last_state == state:
            raise pyxb.LogicError('Unexpected external dependency in sibling namespaces: %s' % (six.u('\n  ').join( [six.text_type(_ns) for _ns in need_resolved_set ]),))
        last_state = state

@six.python_2_unicode_compatible
class NamespaceContext (object):
    """Records information associated with namespaces at a DOM node.
    """

    def __str__ (self):
        rv = [ six.u('NamespaceContext ') ]
        if self.defaultNamespace() is not None:
            rv.extend([ '(defaultNamespace=', six.text_type(self.defaultNamespace()), ') '])
        if self.targetNamespace() is not None:
            rv.extend([ '(targetNamespace=', six.text_type(self.targetNamespace()), ') '])
        rv.append("\n")
        for (pfx, ns) in six.iteritems(self.inScopeNamespaces()):
            if pfx is not None:
                rv.append('  xmlns:%s=%s' % (pfx, six.text_type(ns)))
        return six.u('').join(rv)

    __ContextStack = []
    @classmethod
    def PushContext (cls, ctx):
        """Make C{ctx} the currently active namespace context.

        Prior contexts are retained on a LIFO stack."""
        assert isinstance(ctx, cls)
        cls.__ContextStack.append(ctx)
        return ctx

    @classmethod
    def Current (cls):
        """Access the currently active namespace context.

        If no context is active, C{None} is returned.  This probably
        represents mis-use of the infrastructure (viz., failure to record the
        context within which a QName must be resolved)."""
        if cls.__ContextStack:
            return cls.__ContextStack[-1]
        return None

    @classmethod
    def PopContext (cls):
        """Discard the currently active namespace context, restoring its
        predecessor.

        The discarded context is returned."""
        return cls.__ContextStack.pop()

    __TargetNamespaceAttributes = { }
    @classmethod
    def _AddTargetNamespaceAttribute (cls, expanded_name, attribute_name):
        assert expanded_name is not None
        cls.__TargetNamespaceAttributes[expanded_name] = attribute_name
    @classmethod
    def _TargetNamespaceAttribute (cls, expanded_name):
        return cls.__TargetNamespaceAttributes.get(expanded_name)

    # Support for holding onto referenced namespaces until we have a target
    # namespace to give them to.
    __pendingReferencedNamespaces = None

    def defaultNamespace (self):
        """The default namespace in effect at this node.  E.g., C{xmlns="URN:default"}."""
        return self.__defaultNamespace
    __defaultNamespace = None

    def setDefaultNamespace (self, default_namespace):
        """Set the default namespace for the generated document.

        Even if invoked post construction, the default namespace will affect
        the entire document, as all namespace declarations are placed in the
        document root.

        @param default_namespace: The namespace to be defined as the default
        namespace in the top-level element of the document.  May be provided
        as a real namespace, or just its URI.
        @type default_namespace: L{pyxb.namespace.Namespace} or C{str} or
        C{unicode}.
        """

        if isinstance(default_namespace, six.string_types):
            default_namespace = utility.NamespaceForURI(default_namespace, create_if_missing=True)
        if (default_namespace is not None) and default_namespace.isAbsentNamespace():
            raise pyxb.UsageError('Default namespace must not be an absent namespace')
        self.__defaultNamespace = default_namespace

    # If C{True}, this context is within a schema that has no target
    # namespace, and we should use the target namespace as a fallback if no
    # default namespace is available and no namespace prefix appears on a
    # QName.  This situation arises when a top-level schema has an absent
    # target namespace, or when a schema with an absent target namespace is
    # being included into a schema with a non-absent target namespace.
    __fallbackToTargetNamespace = False

    def targetNamespace (self):
        """The target namespace in effect at this node.  Usually from the
        C{targetNamespace} attribute.  If no namespace is specified for the
        schema, an absent namespace was assigned upon creation and will be
        returned."""
        return self.__targetNamespace
    __targetNamespace = None

    def inScopeNamespaces (self):
        """Map from prefix strings to L{Namespace} instances associated with those
        prefixes.  The prefix C{None} identifies the default namespace."""
        return self.__inScopeNamespaces
    __inScopeNamespaces = None

    """Map from L{Namespace} instances to sets of prefix strings associated
    with the namespace.  The default namespace is not represented."""
    __inScopePrefixes = None

    def __removePrefixMap (self, pfx):
        ns = self.__inScopeNamespaces.pop(pfx, None)
        if ns is not None:
            pfxs = self.__inScopePrefixes.get(ns)
            if pfxs is not None:
                pfxs.discard(pfx)

    def __addPrefixMap (self, pfx, ns):
        # Any previous assignment must have already been removed
        self.__inScopeNamespaces[pfx] = ns
        self.__inScopePrefixes.setdefault(ns, set()).add(pfx)

    def __clonePrefixMap (self):
        self.__inScopeNamespaces = self.__inScopeNamespaces.copy()
        isp = {}
        for (ns, pfxs) in six.iteritems(self.__inScopePrefixes):
            isp[ns] = pfxs.copy()
        self.__inScopePrefixes = isp

    # Class-scope initial map from prefix to namespace
    __InitialScopeNamespaces = None
    # Class-scope initial map from namespace to prefix(es)
    __InitialScopePrefixes = None
    # Instance-specific initial map from prefix to namespace
    __initialScopeNamespaces = None
    # Instance-specific initial map from namespace to prefix(es)
    __initialScopePrefixes = None


    @classmethod
    def __BuildInitialPrefixMap (cls):
        if cls.__InitialScopeNamespaces is not None:
            return
        from pyxb.namespace import builtin
        cls.__InitialScopeNamespaces = builtin._UndeclaredNamespaceMap
        cls.__InitialScopePrefixes = {}
        for (pfx, ns) in six.iteritems(cls.__InitialScopeNamespaces):
            cls.__InitialScopePrefixes.setdefault(ns, set()).add(pfx)

    def prefixForNamespace (self, namespace):
        """Return a prefix associated with the given namespace in this
        context, or None if the namespace is the default or is not in
        scope."""
        pfxs = self.__inScopePrefixes.get(namespace)
        if pfxs:
            return next(iter(pfxs))
        return None

    @classmethod
    def GetNodeContext (cls, node, **kw):
        """Get the L{NamespaceContext} instance that was assigned to the node.

        If none has been assigned and keyword parameters are present, create
        one treating this as the root node and the keyword parameters as
        configuration information (e.g., default_namespace).

        @raise pyxb.LogicError: no context is available and the keywords
        required to create one were not provided
        """
        try:
            return node.__namespaceContext
        except AttributeError:
            return NamespaceContext(node, **kw)

    def setNodeContext (self, node):
        node.__namespaceContext = self

    # Integer counter to help generate unique namespace prefixes
    __namespacePrefixCounter = None

    def declareNamespace (self, namespace, prefix=None, add_to_map=False):
        """Record the given namespace as one to be used in this document.

        @param namespace: The namespace to be associated with the document.
        @type namespace: L{pyxb.namespace.Namespace}

        @keyword prefix: Optional prefix to be used with this namespace.  If
        not provided, a unique prefix is generated or a standard prefix is
        used, depending on the namespace.

        @return: a prefix that may be used with the namespace.  If C{prefix}
        was C{None} the return value may be a previously-assigned prefix.

        @todo: ensure multiple namespaces do not share the same prefix
        @todo: provide default prefix in L{pyxb.namespace.Namespace}
        """
        if not isinstance(namespace, pyxb.namespace.Namespace):
            raise pyxb.UsageError('declareNamespace: must be given a namespace instance')
        if namespace.isAbsentNamespace():
            raise pyxb.UsageError('declareNamespace: namespace must not be an absent namespace')
        if prefix is None:
            prefix = namespace.prefix()
        if prefix is None:
            pfxs = self.__inScopePrefixes.get(namespace)
            if pfxs:
                prefix = next(iter(pfxs))
        while prefix is None:
            self.__namespacePrefixCounter += 1
            candidate_prefix = 'ns%d' % (self.__namespacePrefixCounter,)
            if not (candidate_prefix in self.__inScopeNamespaces):
                prefix = candidate_prefix
        ns = self.__inScopePrefixes.get(prefix)
        if ns:
            if ns != namespace:
                raise pyxb.LogicError('Prefix %s is already in use for %s' % (prefix, ns))
            return prefix
        if not self.__mutableInScopeNamespaces:
            self.__clonePrefixMap()
            self.__mutableInScopeNamespaces = True
        self.__addPrefixMap(prefix, namespace)
        return prefix

    def processXMLNS (self, prefix, uri):
        from pyxb.namespace import builtin
        if not self.__mutableInScopeNamespaces:
            self.__clonePrefixMap()
            self.__mutableInScopeNamespaces = True
        if builtin.XML.boundPrefix() == prefix:
            # Bound prefix xml is permitted if it's bound to the right URI, or
            # if the scope is being left.  In neither case is the mapping
            # adjusted.
            if (uri is None) or builtin.XML.uri() == uri:
                return
            raise pyxb.LogicError('Cannot manipulate bound prefix xml')
        if uri:
            if prefix is None:
                ns = self.__defaultNamespace = utility.NamespaceForURI(uri, create_if_missing=True)
                self.__inScopeNamespaces[None] = self.__defaultNamespace
            else:
                ns = utility.NamespaceForURI(uri, create_if_missing=True)
                self.__removePrefixMap(prefix)
                self.__addPrefixMap(prefix, ns)
            if self.__targetNamespace:
                self.__targetNamespace._referenceNamespace(ns)
            else:
                self.__pendingReferencedNamespaces.add(ns)
        else:
            # NB: XMLNS 6.2 says that you can undefine a default
            # namespace, but does not say anything explicitly about
            # undefining a prefixed namespace.  XML-Infoset 2.2
            # paragraph 6 implies you can do this, but expat blows up
            # if you try it.  I don't think it's legal.
            if prefix is not None:
                raise pyxb.NamespaceError(self, 'Attempt to undefine non-default namespace %s' % (prefix,))
            self.__removePrefixMap(prefix)
            self.__defaultNamespace = None

    def finalizeTargetNamespace (self, tns_uri=None, including_context=None):
        if tns_uri is not None:
            assert 0 < len(tns_uri)
            # Do not prevent overwriting target namespace; need this for WSDL
            # files where an embedded schema inadvertently inherits a target
            # namespace from its enclosing definitions element.  Note that if
            # we don't check this here, we do have to check it when schema
            # documents are included into parent schema documents.
            self.__targetNamespace = utility.NamespaceForURI(tns_uri, create_if_missing=True)
        elif self.__targetNamespace is None:
            if including_context is not None:
                self.__targetNamespace = including_context.targetNamespace()
                self.__fallbackToTargetNamespace = True
            elif tns_uri is None:
                self.__targetNamespace = utility.CreateAbsentNamespace()
            else:
                self.__targetNamespace = utility.NamespaceForURI(tns_uri, create_if_missing=True)
        if self.__pendingReferencedNamespaces is not None:
            [ self.__targetNamespace._referenceNamespace(_ns) for _ns in self.__pendingReferencedNamespaces ]
            self.__pendingReferencedNamespace = None
        assert self.__targetNamespace is not None
        if (not self.__fallbackToTargetNamespace) and self.__targetNamespace.isAbsentNamespace():
            self.__fallbackToTargetNamespace = True

    def reset (self):
        """Reset this instance to the state it was when created, exclusive of
        XMLNS directives passed in a constructor C{dom_node} parameter.

        This preserves parent context and constructor-specified prefix maps,
        but clears the namespace-prefix mapping of any additions made while
        processing namespace directives in DOM nodes, or manually added
        post-construction.

        The defaultNamespace is also retained."""
        self.__inScopeNamespaces = self.__initialScopeNamespaces
        self.__inScopePrefixes = self.__initialScopePrefixes
        self.__mutableInScopeNamespaces = False
        self.__namespacePrefixCounter = 0

    def __init__ (self,
                  dom_node=None,
                  parent_context=None,
                  including_context=None,
                  recurse=True,
                  default_namespace=None,
                  target_namespace=None,
                  in_scope_namespaces=None,
                  expanded_name=None,
                  finalize_target_namespace=True):  # MUST BE True for WSDL to work with minidom
        """Determine the namespace context that should be associated with the
        given node and, optionally, its element children.

        Primarily this class maintains a map between namespaces and prefixes
        used in QName instances.  The initial map comprises the bound prefixes
        (C{xml} and C{xmlns}), prefixes inherited from C{parent_context}, and
        prefixes passed through the C{in_scope_namespaces}
        parameter to the constructor.  This map is then augmented by any
        namespace declarations present in a passed C{dom_node}.  The initial
        map prior to augmentation may be restored through the L{reset()}
        method.

        @param dom_node: The DOM node
        @type dom_node: C{xml.dom.Element}
        @keyword parent_context: Optional value that specifies the context
        associated with C{dom_node}'s parent node.  If not provided, only the
        C{xml} namespace is in scope.
        @type parent_context: L{NamespaceContext}
        @keyword recurse: If True (default), create namespace contexts for all
        element children of C{dom_node}
        @type recurse: C{bool}
        @keyword default_namespace: Optional value to set as the default
        namespace.  Values from C{parent_context} would override this, as
        would an C{xmlns} attribute in the C{dom_node}.
        @type default_namespace: L{NamespaceContext}
        @keyword target_namespace: Optional value to set as the target
        namespace.  Values from C{parent_context} would override this, as
        would a C{targetNamespace} attribute in the C{dom_node}
        @type target_namespace: L{NamespaceContext}
        @keyword in_scope_namespaces: Optional value to set as the initial set
        of in-scope namespaces.  The always-present namespaces are added to
        this if necessary.
        @type in_scope_namespaces: C{dict} mapping prefix C{string} to L{Namespace}.
        """
        from pyxb.namespace import builtin

        if dom_node is not None:
            try:
                assert dom_node.__namespaceContext is None
            except AttributeError:
                pass
            dom_node.__namespaceContext = self

        self.__defaultNamespace = default_namespace
        self.__targetNamespace = target_namespace
        if self.__InitialScopeNamespaces is None:
            self.__BuildInitialPrefixMap()
        self.__inScopeNamespaces = self.__InitialScopeNamespaces
        self.__inScopePrefixes = self.__InitialScopePrefixes
        self.__mutableInScopeNamespaces = False
        self.__namespacePrefixCounter = 0

        if parent_context is not None:
            self.__inScopeNamespaces = parent_context.__inScopeNamespaces
            self.__inScopePrefixes = parent_context.__inScopePrefixes
            if parent_context.__mutableInScopeNamespaces:
                self.__clonePrefixMap()
            self.__defaultNamespace = parent_context.defaultNamespace()
            self.__targetNamespace = parent_context.targetNamespace()
            self.__fallbackToTargetNamespace = parent_context.__fallbackToTargetNamespace
        if in_scope_namespaces is not None:
            self.__clonePrefixMap()
            self.__mutableInScopeNamespaces = True
            for (pfx, ns) in six.iteritems(in_scope_namespaces):
                self.__removePrefixMap(pfx)
                self.__addPrefixMap(pfx, ns)

        # Record a copy of the initial mapping, exclusive of namespace
        # directives from C{dom_node}, so we can reset to that state.
        self.__initialScopeNamespaces = self.__inScopeNamespaces
        self.__initialScopePrefixes = self.__inScopePrefixes
        self.__mutableInScopeNamespaces = False

        if self.__targetNamespace is None:
            self.__pendingReferencedNamespaces = set()
        attribute_map = {}
        if dom_node is not None:
            if expanded_name is None:
                expanded_name = pyxb.namespace.ExpandedName(dom_node)
            for ai in range(dom_node.attributes.length):
                attr = dom_node.attributes.item(ai)
                if builtin.XMLNamespaces.uri() == attr.namespaceURI:
                    prefix = attr.localName
                    if 'xmlns' == prefix:
                        prefix = None
                    self.processXMLNS(prefix, attr.value)
                else:
                    if attr.namespaceURI is not None:
                        uri = utility.NamespaceForURI(attr.namespaceURI, create_if_missing=True)
                        key = pyxb.namespace.ExpandedName(uri, attr.localName)
                    else:
                        key = pyxb.namespace.ExpandedName(None, attr.localName)
                    attribute_map[key] = attr.value

        if finalize_target_namespace:
            tns_uri = None
            tns_attr = self._TargetNamespaceAttribute(expanded_name)
            if tns_attr is not None:
                tns_uri = attribute_map.get(tns_attr)
                self.finalizeTargetNamespace(tns_uri, including_context=including_context)

        # Store in each node the in-scope namespaces at that node;
        # we'll need them for QName interpretation of attribute
        # values.
        if (dom_node is not None) and recurse:
            from xml.dom import Node
            assert Node.ELEMENT_NODE == dom_node.nodeType
            for cn in dom_node.childNodes:
                if Node.ELEMENT_NODE == cn.nodeType:
                    NamespaceContext(dom_node=cn, parent_context=self, recurse=True)

    def interpretQName (self, name, namespace=None, default_no_namespace=False):
        """Convert the provided name into an L{ExpandedName}, i.e. a tuple of
        L{Namespace} and local name.

        If the name includes a prefix, that prefix must map to an in-scope
        namespace in this context.  Absence of a prefix maps to
        L{defaultNamespace()}, which must be provided (or defaults to the
        target namespace, if that is not absent).

        @param name: A QName.
        @type name: C{str} or C{unicode}
        @param name: Optional namespace to use for unqualified names when
        there is no default namespace.  Note that a defined default namespace,
        even if absent, supersedes this value.
        @keyword default_no_namespace: If C{False} (default), an NCName in a
        context where C{namespace} is C{None} and no default or fallback
        namespace can be identified produces an exception.  If C{True}, such an
        NCName is implicitly placed in no namespace.
        @return: An L{ExpandedName} tuple: ( L{Namespace}, C{str} )
        @raise pyxb.QNameResolutionError: The prefix is not in scope
        @raise pyxb.QNameResolutionError: No prefix is given and the default namespace is absent
        """
        if isinstance(name, pyxb.namespace.ExpandedName):
            return name
        assert isinstance(name, six.string_types)
        if 0 <= name.find(':'):
            (prefix, local_name) = name.split(':', 1)
            assert self.inScopeNamespaces() is not None
            namespace = self.inScopeNamespaces().get(prefix)
            if namespace is None:
                raise pyxb.QNameResolutionError('No namespace declaration for prefix', name, self)
        else:
            local_name = name
            # Context default supersedes caller-provided namespace
            if self.defaultNamespace() is not None:
                namespace = self.defaultNamespace()
            # If there's no default namespace, but there is a fallback
            # namespace, use that instead.
            if (namespace is None) and self.__fallbackToTargetNamespace:
                namespace = self.targetNamespace()
            if (namespace is None) and not default_no_namespace:
                raise pyxb.QNameResolutionError('NCName with no fallback/default namespace cannot be resolved', name, self)
        return pyxb.namespace.ExpandedName(namespace, local_name)

    def queueForResolution (self, component, depends_on=None):
        """Forwards to L{queueForResolution()<Namespace.queueForResolution>} in L{targetNamespace()}."""
        assert isinstance(component, _Resolvable_mixin)
        return self.targetNamespace().queueForResolution(component, depends_on)

## Local Variables:
## fill-column:78
## End:
