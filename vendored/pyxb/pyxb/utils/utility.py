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

"""Utility functions and classes."""

import re
import os
import errno
import pyxb
from pyxb.utils.six.moves.urllib import parse as urlparse
import time
import datetime
import logging
from pyxb.utils import six

_log = logging.getLogger(__name__)

class Object (object):
    """A dummy class used to hold arbitrary attributes.

    Essentially this gives us a map without having to worry about
    converting names to text to use as keys.
    """
    pass

def BackfillComparisons (cls):
    """Class decorator that fills in missing ordering methods.

    Concept derived from Python 2.7.5 functools.total_ordering,
    but this version requires that __eq__ and __lt__ be provided,
    and unconditionally overrides __ne__, __gt__, __le__, and __ge__
    with the derived versions.

    This is still necessary in Python 3 because in Python 3 the
    comparison x >= y is done by the __ge__ inherited from object,
    which does not handle the case where x and y are not the same type
    even if the underlying y < x would convert x to be compatible. """

    def applyconvert (cls, derived):
        for (opn, opx) in derived:
            opx.__name__ = opn
            opx.__doc__ = getattr(int, opn).__doc__
            setattr(cls, opn, opx)

    applyconvert(cls, (
            ('__gt__', lambda self, other: not (self.__lt__(other) or self.__eq__(other))),
            ('__le__', lambda self, other: self.__lt__(other) or self.__eq__(other)),
            ('__ge__', lambda self, other: not self.__lt__(other))
            ))
    applyconvert(cls, (
            ('__ne__', lambda self, other: not self.__eq__(other)),
            ))
    return cls

def IteratedCompareMixed (lhs, rhs):
    """Tuple comparison that permits C{None} as lower than any value,
    and defines other cross-type comparison.

    @return: -1 if lhs < rhs, 0 if lhs == rhs, 1 if lhs > rhs."""
    li = iter(lhs)
    ri = iter(rhs)
    while True:
        try:
            (lv, rv) = (next(li), next(ri))
            if lv is None:
                if rv is None:
                    continue
                return -1
            if rv is None:
                return 1
            if lv == rv:
                continue
            if lv < rv:
                return -1
            return 1
        except StopIteration:
            nl = len(lhs)
            nr = len(rhs)
            if nl < nr:
                return -1
            if nl == nr:
                return 0
            return 1

def QuotedEscaped (s):
    """Convert a string into a literal value that can be used in Python source.

    This just calls C{repr}.  No point in getting all complex when the language
    already gives us what we need.

    @rtype: C{str}
    """
    return repr(s)

def _DefaultXMLIdentifierToPython (identifier):
    """Default implementation for _XMLIdentifierToPython

    For historical reasons, this converts the identifier from a str to
    unicode in the system default encoding.  This should have no
    practical effect.

    @param identifier : some XML identifier

    @return: C{unicode(identifier)}
    """

    return six.text_type(identifier)

def _SetXMLIdentifierToPython (xml_identifier_to_python):
    """Configure a callable L{MakeIdentifier} uses to pre-process an XM Lidentifier.

    In Python3, identifiers can be full Unicode tokens, but in Python2,
    all identifiers must be ASCII characters.  L{MakeIdentifier} enforces
    this by removing all characters that are not valid within an
    identifier.

    In some cases, an application generating bindings may be able to
    transliterate Unicode code points that are not valid Python identifier
    characters into something else.  This callable can be assigned to
    perform that translation before the invalid characters are
    stripped.

    It is not the responsibility of this callable to do anything other
    than replace whatever characters it wishes to.  All
    transformations performed by L{MakeIdentifier} will still be
    applied, to ensure the output is in fact a legal identifier.

    @param xml_identifier_to_python : A callable that takes a string
    and returns a Unicode, possibly with non-identifier characters
    replaced by other characters.  Pass C{None} to reset to the
    default implementation, which is L{_DefaultXMLIdentifierToPython}.

    @rtype: C{unicode}
    """
    global _XMLIdentifierToPython
    if xml_identifier_to_python is None:
        xml_identifier_to_python = _DefaultXMLIdentifierToPython
    _XMLIdentifierToPython = xml_identifier_to_python

_XMLIdentifierToPython = _DefaultXMLIdentifierToPython

_UnderscoreSubstitute_re = re.compile(r'[- .]')
_NonIdentifier_re = re.compile(r'[^a-zA-Z0-9_]')
_PrefixUnderscore_re = re.compile(r'^_+')
_PrefixDigit_re = re.compile(r'^\d+')
_CamelCase_re = re.compile(r'_\w')

def MakeIdentifier (s, camel_case=False):
    """Convert a string into something suitable to be a Python identifier.

    The string is processed by L{_XMLIdentifierToPython}.  Following
    this, dashes, spaces, and periods are replaced by underscores, and
    characters not permitted in Python identifiers are stripped.
    Furthermore, any leading underscores are removed.  If the result
    begins with a digit, the character 'n' is prepended.  If the
    result is the empty string, the string 'emptyString' is
    substituted.

    No check is made for L{conflicts with keywords <DeconflictKeyword>}.

    @keyword camel_case : If C{True}, any underscore in the result
    string that is immediately followed by an alphanumeric is replaced
    by the capitalized version of that alphanumeric.  Thus,
    'one_or_two' becomes 'oneOrTwo'.  If C{False} (default), has no
    effect.

    @rtype: C{str}
    """
    s = _XMLIdentifierToPython(s)
    s = _PrefixUnderscore_re.sub('', _NonIdentifier_re.sub('', _UnderscoreSubstitute_re.sub('_', s)))
    if camel_case:
        s = _CamelCase_re.sub(lambda _m: _m.group(0)[1].upper(), s)
    if _PrefixDigit_re.match(s):
        s = 'n' + s
    if 0 == len(s):
        s = 'emptyString'
    return s

def MakeModuleElement (s):
    """Convert a string into something that can be a valid element in a
    Python module path.

    Module path elements are similar to identifiers, but may begin
    with numbers and should not have leading underscores removed.
    """
    return _UnderscoreSubstitute_re.sub('_', _XMLIdentifierToPython(s))

_PythonKeywords = frozenset( (
        "and", "as", "assert", "break", "class", "continue", "def", "del",
        "elif", "else", "except", "exec", "finally", "for", "from", "global",
        "if", "import", "in", "is", "lambda", "not", "or", "pass", "print",
        "raise", "return", "try", "while", "with", "yield"
        ) )
"""Python keywords.  Note that types like int and float are not
keywords.

@see: U{http://docs.python.org/reference/lexical_analysis.html#keywords}."""

_PythonBuiltInConstants = frozenset( (
        "False", "True", "None", "NotImplemented", "Ellipsis", "__debug__",
        # "set" is neither a keyword nor a constant, but if some fool
        # like {http://www.w3.org/2001/SMIL20/}set gets defined there's
        # no way to access the builtin constructor.
        "set"
        ) )
"""Other symbols that aren't keywords but that can't be used.

@see: U{http://docs.python.org/library/constants.html}."""

_Keywords = frozenset(_PythonKeywords.union(_PythonBuiltInConstants))
"""The keywords reserved for Python, derived from L{_PythonKeywords}
and L{_PythonBuiltInConstants}."""

def DeconflictKeyword (s, aux_keywords=frozenset()):
    """If the provided string C{s} matches a Python language keyword,
    append an underscore to distinguish them.

    See also L{MakeUnique}.

    @param s: string to be deconflicted

    @keyword aux_keywords: optional iterable of additional strings
    that should be treated as keywords.

    @rtype: C{str}

    """
    if (s in _Keywords) or (s in aux_keywords):
        return '%s_' % (s,)
    return s

def MakeUnique (s, in_use):
    """Return an identifier based on C{s} that is not in the given set.

    The returned identifier is made unique by appending an underscore
    and, if necessary, a serial number.

    The order is : C{x}, C{x_}, C{x_2}, C{x_3}, ...

    @param in_use: The set of identifiers already in use in the
    relevant scope.  C{in_use} is updated to contain the returned
    identifier.

    @rtype: C{str}
    """
    if s in in_use:
        ctr = 2
        s = s.rstrip('_')
        candidate = '%s_' % (s,)
        while candidate in in_use:
            candidate = '%s_%d' % (s, ctr)
            ctr += 1
        s = candidate
    in_use.add(s)
    return s

def PrepareIdentifier (s, in_use, aux_keywords=frozenset(), private=False, protected=False):
    """Combine everything required to create a unique identifier.

    Leading and trailing underscores are stripped from all
    identifiers.

    @param in_use: the set of already used identifiers.  Upon return
    from this function, it is updated to include the returned
    identifier.

    @keyword aux_keywords: an optional set of additional symbols that
    are illegal in the given context; use this to prevent conflicts
    with known method names.

    @keyword private: if C{False} (default), all leading underscores
    are stripped, guaranteeing the identifier will not be private.  If
    C{True}, the returned identifier has two leading underscores,
    making it a private variable within a Python class.

    @keyword protected: as for C{private}, but uses only one
    underscore.

    @rtype: C{str}

    @note: Only module-level identifiers should be treated as
    protected.  The class-level L{_DeconflictSymbols_mixin}
    infrastructure does not include protected symbols.  All class and
    instance members beginning with a single underscore are reserved
    for the PyXB infrastructure."""
    s = DeconflictKeyword(MakeIdentifier(s).strip('_'), aux_keywords)
    if private:
        s = '__' + s
    elif protected:
        s = '_' + s
    return MakeUnique(s, in_use)

# @todo: descend from pyxb.cscRoot, if we import pyxb
class _DeconflictSymbols_mixin (object):
    """Mix-in used to deconflict public symbols in classes that may be
    inherited by generated binding classes.

    Some classes, like the L{pyxb.binding.basis.element} or
    L{pyxb.binding.basis.simpleTypeDefinition} classes in
    L{pyxb.binding.basis}, have public symbols associated with
    functions and variables.  It is possible that an XML schema might
    include tags and attribute names that match these symbols.  To
    avoid conflict, the reserved symbols marked in this class are
    added to the pre-defined identifier set.

    Subclasses should create a class-level variable
    C{_ReservedSymbols} that contains a set of strings denoting the
    symbols reserved in this class, combined with those from any
    superclasses that also have reserved symbols.  Code like the
    following is suggested::

       # For base classes (direct mix-in):
       _ReservedSymbols = set([ 'one', 'two' ])
       # For subclasses:
       _ReservedSymbols = SuperClass._ReservedSymbols.union(set([ 'three' ]))

    Only public symbols (those with no underscores) are currently
    supported.  (Private symbols can't be deconflicted that easily,
    and no protected symbols that derive from the XML are created by
    the binding generator.)
    """

    _ReservedSymbols = set()
    """There are no reserved symbols in the base class."""

# Regular expression detecting tabs, carriage returns, and line feeds
__TabCRLF_re = re.compile("[\t\n\r]")
# Regular expressoin detecting sequences of two or more spaces
__MultiSpace_re = re.compile(" +")

def NormalizeWhitespace (text, preserve=False, replace=False, collapse=False):
    """Normalize the given string.

    Exactly one of the C{preserve}, C{replace}, and C{collapse} keyword
    parameters must be assigned the value C{True} by the caller.

     - C{preserve}: the text is returned unchanged.

     - C{replace}: all tabs, newlines, and carriage returns are
     replaced with ASCII spaces.

     - C{collapse}: the C{replace} normalization is done, then
     sequences of two or more spaces are replaced by a single space.

    See the U{whiteSpace facet<http://www.w3.org/TR/xmlschema-2/#rf-whiteSpace>}.

    @rtype: C{str}
    """
    if preserve:
        return text
    text = __TabCRLF_re.sub(' ', text)
    if replace:
        return text
    if collapse:
        return __MultiSpace_re.sub(' ', text).strip()
    # pyxb not imported here; could be.
    raise Exception('NormalizeWhitespace: No normalization specified')

class Graph:
    """Represent a directed graph with arbitrary objects as nodes.

    This is used in the L{code
    generator<pyxb.binding.generate.Generator>} to determine order
    dependencies among components within a namespace, and schema that
    comprise various namespaces.  An edge from C{source} to C{target}
    indicates that some aspect of C{source} requires that some aspect
    of C{target} already be available.
    """

    def __init__ (self, root=None):
        self.__roots = None
        if root is not None:
            self.__roots = set([root])
        self.__edges = set()
        self.__edgeMap = { }
        self.__reverseMap = { }
        self.__nodes = set()

    __scc = None
    __sccMap = None
    __dfsOrder = None

    def addEdge (self, source, target):
        """Add a directed edge from the C{source} to the C{target}.

        The nodes are added to the graph if necessary.
        """
        self.__edges.add( (source, target) )
        self.__edgeMap.setdefault(source, set()).add(target)
        if source != target:
            self.__reverseMap.setdefault(target, set()).add(source)
        self.__nodes.add(source)
        self.__nodes.add(target)

    def addNode (self, node):
        """Add  the given node to the graph."""
        self.__nodes.add(node)

    __roots = None
    def roots (self, reset=False):
        """Return the set of nodes calculated to be roots (i.e., those that have no incoming edges).

        This caches the roots calculated in a previous invocation
        unless the C{reset} keyword is given the value C{True}.

        @note: Upon reset, any notes that had been manually added
        using L{addNode} will no longer be in the set.

        @keyword reset: If C{True}, any cached value is discarded and
        recomputed.  No effect if C{False} (defalut).

        @rtype: C{set}
        """
        if reset or (self.__roots is None):
            self.__roots = set()
            for n in self.__nodes:
                if not (n in self.__reverseMap):
                    self.__roots.add(n)
        return self.__roots
    def addRoot (self, root):
        """Add the provided node as a root node, even if it has incoming edges.

        The node need not be present in the graph (if necessary, it is added).

        Note that roots added in this way do not survive a reset using
        L{roots}.

        @return: C{self}
        """
        if self.__roots is None:
            self.__roots = set()
        self.__nodes.add(root)
        self.__roots.add(root)
        return self

    def edgeMap (self):
        """Return the edges in the graph.

        The edge data structure is a map from the source node to the
        set of nodes that can be reached in a single step from the
        source.
        """
        return self.__edgeMap
    __edgeMap = None

    def edges (self):
        """Return the edges in the graph.

        The edge data structure is a set of node pairs represented as C{( source, target )}.
        """
        return self.__edges

    def nodes (self):
        """Return the set of nodes in the graph.

        The node collection data structure is a set containing node
        objects, whatever they may be."""
        return self.__nodes

    def tarjan (self, reset=False):
        """Execute Tarjan's algorithm on the graph.

        U{Tarjan's
        algorithm<http://en.wikipedia.org/wiki/Tarjan%27s_strongly_connected_components_algorithm>}
        computes the U{strongly-connected
        components<http://en.wikipedia.org/wiki/Strongly_connected_component>}
        of the graph: i.e., the sets of nodes that form a minimal
        closed set under edge transition.  In essence, the loops.  We
        use this to detect groups of components that have a dependency
        cycle.

        @keyword reset: If C{True}, any cached component set is erased
        and recomputed.  If C{True}, an existing previous result is
        left unchanged."""

        if (self.__scc is not None) and (not reset):
            return
        self.__sccMap = { }
        self.__stack = []
        self.__sccOrder = []
        self.__scc = []
        self.__index = 0
        self.__tarjanIndex = { }
        self.__tarjanLowLink = { }
        for v in self.__nodes:
            self.__tarjanIndex[v] = None
        roots = self.roots()
        if (0 == len(roots)) and (0 < len(self.__nodes)):
            raise Exception('TARJAN: No roots found in graph with %d nodes' % (len(self.__nodes),))
        for r in roots:
            self._tarjan(r)
        self.__didTarjan = True

    def _tarjan (self, v):
        """Do the work of Tarjan's algorithm for a given root node."""
        if self.__tarjanIndex.get(v) is not None:
            # "Root" was already reached.
            return
        self.__tarjanIndex[v] = self.__tarjanLowLink[v] = self.__index
        self.__index += 1
        self.__stack.append(v)
        source = v
        for target in self.__edgeMap.get(source, []):
            if self.__tarjanIndex[target] is None:
                self._tarjan(target)
                self.__tarjanLowLink[v] = min(self.__tarjanLowLink[v], self.__tarjanLowLink[target])
            elif target in self.__stack:
                self.__tarjanLowLink[v] = min(self.__tarjanLowLink[v], self.__tarjanLowLink[target])
            else:
                pass

        if self.__tarjanLowLink[v] == self.__tarjanIndex[v]:
            scc = []
            while True:
                scc.append(self.__stack.pop())
                if v == scc[-1]:
                    break
            self.__sccOrder.append(scc)
            if 1 < len(scc):
                self.__scc.append(scc)
                [ self.__sccMap.setdefault(_v, scc) for _v in scc ]

    def scc (self, reset=False):
        """Return the strongly-connected components of the graph.

        The data structure is a set, each element of which is itself a
        set containing one or more nodes from the graph.

        @see: L{tarjan}.
        """
        if reset or (self.__scc is None):
            self.tarjan(reset)
        return self.__scc
    __scc = None

    def sccMap (self, reset=False):
        """Return a map from nodes to the strongly-connected component
        to which the node belongs.

        @keyword reset: If C{True}, the L{tarjan} method will be
        re-invoked, propagating the C{reset} value.  If C{False}
        (default), a cached value will be returned if available.

        @see: L{tarjan}.
        """
        if reset or (self.__sccMap is None):
            self.tarjan(reset)
        return self.__sccMap
    __sccMap = None

    def sccOrder (self, reset=False):
        """Return the strongly-connected components in order.

        The data structure is a list, in dependency order, of strongly
        connected components (which can be single nodes).  Appearance
        of a node in a set earlier in the list indicates that it has
        no dependencies on any node that appears in a subsequent set.
        This order is preferred over L{dfsOrder} for code generation,
        since it detects loops.

        @see: L{tarjan}.
        """
        if reset or (self.__sccOrder is None):
            self.tarjan(reset)
        return self.__sccOrder
    __sccOrder = None

    def sccForNode (self, node, **kw):
        """Return the strongly-connected component to which the given
        node belongs.

        Any keywords suppliend when invoking this method are passed to
        the L{sccMap} method.

        @return: The SCC set, or C{None} if the node is not present in
        the results of Tarjan's algorithm."""

        return self.sccMap(**kw).get(node)

    def cyclomaticComplexity (self):
        """Return the cyclomatic complexity of the graph."""
        self.tarjan()
        return len(self.__edges) - len(self.__nodes) + 2 * len(self.__scc)

    def __dfsWalk (self, source):
        assert not (source in self.__dfsWalked)
        self.__dfsWalked.add(source)
        for target in self.__edgeMap.get(source, []):
            if not (target in self.__dfsWalked):
                self.__dfsWalk(target)
        self.__dfsOrder.append(source)

    def _generateDOT (self, title='UNKNOWN', labeller=None):
        node_map = { }
        idx = 1
        for n in self.__nodes:
            node_map[n] = idx
            idx += 1
        text = []
        text.append('digraph "%s" {' % (title,))
        for n in self.__nodes:
            if labeller is not None:
                nn = labeller(n)
            else:
                nn = str(n)
            text.append('%s [shape=box,label="%s"];' % (node_map[n], nn))
        for s in self.__nodes:
            for d in self.__edgeMap.get(s, []):
                if s != d:
                    text.append('%s -> %s;' % (node_map[s], node_map[d]))
        text.append("};")
        return "\n".join(text)

    def dfsOrder (self, reset=False):
        """Return the nodes of the graph in U{depth-first-search
        order<http://en.wikipedia.org/wiki/Depth-first_search>}.

        The data structure is a list.  Calculated lists are retained
        and returned on future invocations, subject to the C{reset}
        keyword.

        @keyword reset: If C{True}, discard cached results and recompute the order."""
        if reset or (self.__dfsOrder is None):
            self.__dfsWalked = set()
            self.__dfsOrder = []
            for root in self.roots(reset=reset):
                self.__dfsWalk(root)
            self.__dfsWalked = None
            if len(self.__dfsOrder) != len(self.__nodes):
                raise Exception('DFS walk did not cover all nodes (walk %d versus nodes %d)' % (len(self.__dfsOrder), len(self.__nodes)))
        return self.__dfsOrder

    def rootSetOrder (self):
        """Return the nodes of the graph as a sequence of root sets.

        The first root set is the set of nodes that are roots: i.e.,
        have no incoming edges.  The second root set is the set of
        nodes that have incoming nodes in the first root set.  This
        continues until all nodes have been reached.  The sets impose
        a partial order on the nodes, without being as constraining as
        L{sccOrder}.

        @return: a list of the root sets."""
        order = []
        nodes = set(self.__nodes)
        edge_map = {}
        for (d, srcs) in six.iteritems(self.__edgeMap):
            edge_map[d] = srcs.copy()
        while nodes:
            freeset = set()
            for n in nodes:
                if not (n in edge_map):
                    freeset.add(n)
            if 0 == len(freeset):
                _log.error('dependency cycle in named components')
                return None
            order.append(freeset)
            nodes.difference_update(freeset)
            new_edge_map = {}
            for (d, srcs) in six.iteritems(edge_map):
                srcs.difference_update(freeset)
                if 0 != len(srcs):
                    new_edge_map[d] = srcs
            edge_map = new_edge_map
        return order

LocationPrefixRewriteMap_ = { }

def SetLocationPrefixRewriteMap (prefix_map):
    """Set the map that is used to by L{NormalizeLocation} to rewrite URI prefixes."""

    LocationPrefixRewriteMap_.clear()
    LocationPrefixRewriteMap_.update(prefix_map)

def NormalizeLocation (uri, parent_uri=None, prefix_map=None):
    """Normalize a URI against an optional parent_uri in the way that is
    done for C{schemaLocation} attribute values.

    If no URI schema is present, this will normalize a file system
    path.

    Optionally, the resulting absolute URI can subsequently be
    rewritten to replace specified prefix strings with alternative
    strings, e.g. to convert a remote URI to a local repository.  This
    rewriting is done after the conversion to an absolute URI, but
    before normalizing file system URIs.

    @param uri : The URI to normalize.  If C{None}, function returns
    C{None}

    @param parent_uri : The base URI against which normalization is
    done, if C{uri} is a relative URI.

    @param prefix_map : A map used to rewrite URI prefixes.  If
    C{None}, the value defaults to that stored by
    L{SetLocationPrefixRewriteMap}.

    """
    if uri is None:
        return uri
    if parent_uri is None:
        abs_uri = uri
    else:
        abs_uri = urlparse.urljoin(parent_uri, uri)
    if prefix_map is None:
        prefix_map = LocationPrefixRewriteMap_
    for (pfx, sub) in six.iteritems(prefix_map):
        if abs_uri.startswith(pfx):
            abs_uri = sub + abs_uri[len(pfx):]
    if 0 > abs_uri.find(':'):
        abs_uri = os.path.realpath(abs_uri)
    return abs_uri


def DataFromURI (uri, archive_directory=None):
    """Retrieve the contents of the uri as raw data.

    If the uri does not include a scheme (e.g., C{http:}), it is
    assumed to be a file path on the local system."""

    from pyxb.utils.six.moves.urllib.request import urlopen
    stream = None
    exc = None
    # Only something that has a colon is a non-file URI.  Some things
    # that have a colon are a file URI (sans schema).  Prefer urllib2,
    # but allow urllib (which apparently works better on Windows).
    if 0 <= uri.find(':'):
        try:
            stream = urlopen(uri)
        except Exception as e:
            exc = e
        if (stream is None) and six.PY2:
            import urllib
            try:
                stream = urllib.urlopen(uri)
                exc = None
            except:
                # Prefer urllib exception
                pass
    if stream is None:
        # No go as URI; give file a chance
        try:
            stream = open(uri, 'rb')
            exc = None
        except Exception as e:
            if exc is None:
                exc = e
    if exc is not None:
        _log.error('open %s', uri, exc_info=exc)
        raise exc
    try:
        # Protect this in case whatever stream is doesn't have an fp
        # attribute.
        if isinstance(stream, six.moves.file) or isinstance(stream.fp, six.moves.file):
            archive_directory = None
    except:
        pass
    xmld = stream.read()
    if archive_directory:
        base_name = os.path.basename(os.path.normpath(urlparse.urlparse(uri)[2]))
        counter = 1
        dest_file = os.path.join(archive_directory, base_name)
        while os.path.isfile(dest_file):
            dest_file = os.path.join(archive_directory, '%s.%d' % (base_name, counter))
            counter += 1
        try:
            OpenOrCreate(dest_file).write(xmld)
        except OSError as e:
            _log.warning('Unable to save %s in %s: %s', uri, dest_file, e)
    return xmld

def OpenOrCreate (file_name, tag=None, preserve_contents=False):
    """Return a file object used to write binary data into the given file.

    Use the C{tag} keyword to preserve the contents of existing files
    that are not supposed to be overwritten.

    To get a writable file but leaving any existing contents in place,
    set the C{preserve_contents} keyword to C{True}.  Normally, existing file
    contents are erased.

    The returned file pointer is positioned at the end of the file.

    @keyword tag: If not C{None} and the file already exists, absence
    of the given value in the first 4096 bytes of the file (decoded as
    UTF-8) causes an C{IOError} to be raised with C{errno} set to
    C{EEXIST}.  I.e., only files with this value in the first 4KB will
    be returned for writing.

    @keyword preserve_contents: This value controls whether existing
    contents of the file will be erased (C{False}, default) or left in
    place (C{True}).
    """
    (path, leaf) = os.path.split(file_name)
    if path:
        try:
            os.makedirs(path)
        except Exception as e:
            if not (isinstance(e, (OSError, IOError)) and (errno.EEXIST == e.errno)):
                raise
    fp = open(file_name, 'ab+')
    if (tag is not None) and (0 < os.fstat(fp.fileno()).st_size):
        fp.seek(0) # os.SEEK_SET
        blockd = fp.read(4096)
        blockt = blockd.decode('utf-8')
        if 0 > blockt.find(tag):
            raise OSError(errno.EEXIST, os.strerror(errno.EEXIST))
    if not preserve_contents:
        fp.seek(0) # os.SEEK_SET
        fp.truncate()
    else:
        fp.seek(2) # os.SEEK_END
    return fp

# hashlib didn't show up until 2.5, and sha is deprecated in 2.6.
__Hasher = None
try:
    import hashlib
    __Hasher = hashlib.sha1
except ImportError:
    import sha
    __Hasher = sha.new

def HashForText (text):
    """Calculate a cryptographic hash of the given string.

    For example, this is used to verify that a given module file
    contains bindings from a previous generation run for the same
    namespace.  See L{OpenOrCreate}.  If the text is in Unicode, the
    hash is calculated on the UTF-8 encoding of the text.

    @return: A C{str}, generally a sequence of hexadecimal "digit"s.
    """
    if isinstance(text, six.text_type):
        text = text.encode('utf-8')
    return __Hasher(text).hexdigest()

# uuid didn't show up until 2.5
__HaveUUID = False
try:
    import uuid
    __HaveUUID = True
except ImportError:
    import random
def _NewUUIDString ():
    """Obtain a UUID using the best available method.  On a version of
    python that does not incorporate the C{uuid} class, this creates a
    string combining the current date and time (to the second) with a
    random number.

    @rtype: C{str}
    """
    if __HaveUUID:
        return uuid.uuid1().urn
    return '%s:%08.8x' % (time.strftime('%Y%m%d%H%M%S'), random.randint(0, 0xFFFFFFFF))

class UniqueIdentifier (object):
    """Records a unique identifier, generally associated with a
    binding generation action.

    The identifier is a string, but gets wrapped in an instance of
    this class to optimize comparisons and reduce memory footprint.

    Invoking the constructor for this class on the same string
    multiple times will return the same Python object.

    An instance of this class compares equal to, and hashes equivalent
    to, the uid string.  When C{str}'d, the result is the uid; when
    C{repr}'d, the result is a constructor call to
    C{pyxb.utils.utility.UniqueIdentifier}.
    """

    # A map from UID string to the instance that represents it
    __ExistingUIDs = {}

    def uid (self):
        """The string unique identifier"""
        return self.__uid
    __uid = None

    # Support pickling, which is done using only the UID.
    def __getnewargs__ (self):
        return (self.__uid,)

    def __getstate__ (self):
        return self.__uid

    def __setstate__ (self, state):
        assert self.__uid == state

    # Singleton-like
    def __new__ (cls, *args):
        if 0 == len(args):
            uid = _NewUUIDString()
        else:
            uid = args[0]
        if isinstance(uid, UniqueIdentifier):
            uid = uid.uid()
        if not isinstance(uid, six.string_types):
            raise TypeError('UniqueIdentifier uid must be a string')
        rv = cls.__ExistingUIDs.get(uid)
        if rv is None:
            rv = super(UniqueIdentifier, cls).__new__(cls)
            rv.__uid = uid
            cls.__ExistingUIDs[uid] = rv
        return rv

    def associateObject (self, obj):
        """Associate the given object witth this identifier.

        This is a one-way association: the object is not provided with
        a return path to this identifier instance."""
        self.__associatedObjects.add(obj)
    def associatedObjects (self):
        """The set of objects that have been associated with this
        identifier instance."""
        return self.__associatedObjects
    __associatedObjects = None

    def __init__ (self, uid=None):
        """Create a new UniqueIdentifier instance.

        @param uid: The unique identifier string.  If present, it is
        the callers responsibility to ensure the value is universally
        unique.  If C{None}, one will be provided.
        @type uid: C{str} or C{unicode}
        """
        assert (uid is None) or (self.uid() == uid), 'UniqueIdentifier: ctor %s, actual %s' % (uid, self.uid())
        self.__associatedObjects = set()

    def __eq__ (self, other):
        if other is None:
            return False
        elif isinstance(other, UniqueIdentifier):
            other_uid = other.uid()
        elif isinstance(other, six.string_types):
            other_uid = other
        else:
            raise TypeError('UniqueIdentifier: Cannot compare with type %s' % (type(other),))
        return self.uid() == other_uid

    def __hash__ (self):
        return hash(self.uid())

    def __str__ (self):
        return self.uid()

    def __repr__ (self):
        return 'pyxb.utils.utility.UniqueIdentifier(%s)' % (repr(self.uid()),)

@BackfillComparisons
class UTCOffsetTimeZone (datetime.tzinfo):
    """A C{datetime.tzinfo} subclass that helps deal with UTC
    conversions in an ISO8601 world.

    This class only supports fixed offsets from UTC.
    """

    # Regular expression that matches valid ISO8601 time zone suffixes
    __Lexical_re = re.compile('^([-+])(\d\d):(\d\d)$')

    # The offset in minutes east of UTC.
    __utcOffset_min = 0

    # Same as __utcOffset_min, but as a datetime.timedelta
    __utcOffset_td = None

    # A zero-length duration
    __ZeroDuration = datetime.timedelta(0)

    # Range limits
    __MaxOffset_td = datetime.timedelta(hours=14)

    def __init__ (self, spec=None):
        """Create a time zone instance with a fixed offset from UTC.

        @param spec: Specifies the offset.  Can be an integer counting
        minutes east of UTC, the value C{None} (equal to 0 minutes
        east), or a string that conform to the ISO8601 time zone
        sequence (B{Z}, or B{[+-]HH:MM}).
        """

        if spec is not None:
            if isinstance(spec, six.string_types):
                if 'Z' == spec:
                    self.__utcOffset_min = 0
                else:
                    match = self.__Lexical_re.match(spec)
                    if match is None:
                        raise ValueError('Bad time zone: %s' % (spec,))
                    self.__utcOffset_min = int(match.group(2)) * 60 + int(match.group(3))
                    if '-' == match.group(1):
                        self.__utcOffset_min = - self.__utcOffset_min
            elif isinstance(spec, int):
                self.__utcOffset_min = spec
            elif isinstance(spec, datetime.timedelta):
                self.__utcOffset_min = spec.seconds // 60
            else:
                raise TypeError('%s: unexpected type %s' % (type(self), type(spec)))
        self.__utcOffset_td = datetime.timedelta(minutes=self.__utcOffset_min)
        if self.__utcOffset_td < -self.__MaxOffset_td or self.__utcOffset_td > self.__MaxOffset_td:
            raise ValueError('XSD timezone offset %s larger than %s' % (self.__utcOffset_td, self.__MaxOffset_td))
        if 0 == self.__utcOffset_min:
            self.__tzName = 'Z'
        elif 0 > self.__utcOffset_min:
            self.__tzName = '-%02d:%02d' % divmod(-self.__utcOffset_min, 60)
        else:
            self.__tzName = '+%02d:%02d' % divmod(self.__utcOffset_min, 60)

    def utcoffset (self, dt):
        """Returns the constant offset for this zone."""
        return self.__utcOffset_td

    def tzname (self, dt):
        """Return the name of the timezone in the format expected by XML Schema."""
        return self.__tzName

    def dst (self, dt):
        """Returns a constant zero duration."""
        return self.__ZeroDuration

    def __otherForComparison (self, other):
        if isinstance(other, UTCOffsetTimeZone):
            return other.__utcOffset_min
        return other.utcoffset(datetime.datetime.now())

    def __hash__ (self):
        return hash(self.__utcOffset_min)

    def __eq__ (self, other):
        return self.__utcOffset_min == self.__otherForComparison(other)

    def __lt__ (self, other):
        return self.__utcOffset_min < self.__otherForComparison(other)

class LocalTimeZone (datetime.tzinfo):
    """A C{datetime.tzinfo} subclass for the local time zone.

    Mostly pinched from the C{datetime.tzinfo} documentation in Python 2.5.1.
    """

    __STDOffset = datetime.timedelta(seconds=-time.timezone)
    __DSTOffset = __STDOffset
    if time.daylight:
        __DSTOffset = datetime.timedelta(seconds=-time.altzone)
    __ZeroDelta = datetime.timedelta(0)
    __DSTDelta = __DSTOffset - __STDOffset

    def utcoffset (self, dt):
        if self.__isDST(dt):
            return self.__DSTOffset
        return self.__STDOffset

    def dst (self, dt):
        if self.__isDST(dt):
            return self.__DSTDelta
        return self.__ZeroDelta

    def tzname (self, dt):
        return time.tzname[self.__isDST(dt)]

    def __isDST (self, dt):
        tt = (dt.year, dt.month, dt.day,
              dt.hour, dt.minute, dt.second,
              0, 0, -1)
        tt = time.localtime(time.mktime(tt))
        return tt.tm_isdst > 0

class PrivateTransient_mixin (pyxb.cscRoot):
    """Emulate the B{transient} keyword from Java for private member
    variables.

    This class defines a C{__getstate__} method which returns a copy
    of C{self.__dict__} with certain members removed.  Specifically,
    if a string "s" appears in a class member variable named
    C{__PrivateTransient} defined in the "Class" class, then the
    corresponding private variable "_Class__s" will be removed from
    the state dictionary.  This is used to eliminate unnecessary
    fields from instances placed in L{namespace
    archives<pyxb.namespace.archive.NamespaceArchive>} without having
    to implement a C{__getstate__} method in every class in the
    instance hierarchy.

    For an example, see
    L{pyxb.xmlschema.structures._SchemaComponent_mixin}

    If you use this, it is your responsibility to define the
    C{__PrivateTransient} class variable and add to it the required
    variable names.

    Classes that inherit from this are free to define their own
    C{__getstate__} method, which may or may not invoke the superclass
    one.  If you do this, be sure that the class defining
    C{__getstate__} lists L{PrivateTransient_mixin} as one of its
    direct superclasses, lest the latter end up earlier in the mro and
    consequently bypass the local override.
    """

    # Suffix used when creating the class member variable in which the
    # transient members are cached.
    __Attribute = '__PrivateTransient'

    def __getstate__ (self):
        state = self.__dict__.copy()
        # Note that the aggregate set is stored in a class variable
        # with a slightly different name than the class-level set.
        attr = '_%s%s_' % (self.__class__.__name__, self.__Attribute)
        skipped = getattr(self.__class__, attr, None)
        if skipped is None:
            skipped = set()
            for cl in self.__class__.mro():
                for (k, v) in six.iteritems(cl.__dict__):
                    if k.endswith(self.__Attribute):
                        cl2 = k[:-len(self.__Attribute)]
                        skipped.update([ '%s__%s' % (cl2, _n) for _n in v ])
            setattr(self.__class__, attr, skipped)
        for k in skipped:
            if state.get(k) is not None:
                del state[k]
        # Uncomment the following to test whether undesirable types
        # are being pickled, generally by accidently leaving a
        # reference to one in an instance private member.
        #for (k, v) in six.iteritems(state):
        #    import pyxb.namespace
        #    import xml.dom
        #    import pyxb.xmlschema.structures
        #    if isinstance(v, (pyxb.namespace.NamespaceContext, xml.dom.Node, pyxb.xmlschema.structures.Schema)):
        #        raise pyxb.LogicError('Unexpected instance of %s key %s in %s' % (type(v), k, self))

        return state

def GetMatchingFiles (path, pattern=None, default_path_wildcard=None, default_path=None, prefix_pattern=None, prefix_substituend=None):
    """Provide a list of absolute paths to files present in any of a
    set of directories and meeting certain criteria.

    This is used, for example, to locate namespace archive files
    within the archive path specified by the user.  One could use::

      files = GetMatchingFiles('&bundles//:+',
                               pattern=re.compile('.*\.wxs$'),
                               default_path_wildcard='+',
                               default_path='/usr/local/pyxb/nsarchives',
                               prefix_pattern='&',
                               prefix_substituend='/opt/pyxb')

    to obtain all files that can be recursively found within
    C{/opt/pyxb/bundles}, or non-recursively within
    C{/usr/local/pyxb/nsarchives}.

    @param path: A list of directories in which the search should be
    performed.  The entries are separated by os.pathsep, which is a
    colon on POSIX platforms and a semi-colon on Windows.  If a path
    entry ends with C{//} regardless of platform, the suffix C{//} is
    stripped and any directory beneath the path is scanned as well,
    recursively.

    @keyword pattern: Optional regular expression object used to
    determine whether a given directory entry should be returned.  If
    left as C{None}, all directory entries will be returned.

    @keyword default_path_wildcard: An optional string which, if
    present as a single directory in the path, is replaced by the
    value of C{default-path}.

    @keyword default_path: A system-defined directory which can be
    restored to the path by placing the C{default_path_wildcard} in
    the C{path}.

    @keyword prefix_pattern: An optional string which, if present at
    the start of a path element, is replaced by the value of
    C{prefix_substituend}.

    @keyword prefix_substituend: A system-defined string (path prefix)
    which can be combined with the user-provided path information to
    identify a file or subdirectory within an installation-specific
    area.
    """
    matching_files = []
    path_set = path.split(os.pathsep)
    while 0 < len(path_set):
        path = path_set.pop(0)
        if default_path_wildcard == path:
            if default_path is not None:
                path_set[0:0] = default_path.split(os.pathsep)
                default_path = None
            continue
        recursive = False
        if (prefix_pattern is not None) and path.startswith(prefix_pattern):
            path = os.path.join(prefix_substituend, path[len(prefix_pattern):])
        if path.endswith('//'):
            recursive = True
            path = path[:-2]
        if os.path.isfile(path):
            if (pattern is None) or (pattern.search(path) is not None):
                matching_files.append(path)
        else:
            for (root, dirs, files) in os.walk(path):
                for f in files:
                    if (pattern is None) or (pattern.search(f) is not None):
                        matching_files.append(os.path.join(root, f))
                if not recursive:
                    break
    return matching_files

@BackfillComparisons
class Location (object):
    __locationBase = None
    __lineNumber = None
    __columnNumber = None

    def __init__ (self, location_base=None, line_number=None, column_number=None):
        if isinstance(location_base, str):
            location_base = six.moves.intern(location_base)
        self.__locationBase = location_base
        self.__lineNumber = line_number
        self.__columnNumber = column_number

    def newLocation (self, locator=None, line_number=None, column_number=None):
        if locator is not None:
            try:
                line_number = locator.getLineNumber()
                column_number = locator.getColumnNumber()
            except:
                pass
        return Location(self.__locationBase, line_number, column_number)

    locationBase = property(lambda _s: _s.__locationBase)
    lineNumber = property(lambda _s: _s.__lineNumber)
    columnNumber = property(lambda _s: _s.__columnNumber)

    def __cmpSingleUnlessNone (self, v1, v2):
        if v1 is None:
            if v2 is None:
                return None
            return 1
        if v2 is None:
            return -1
        if v1 < v2:
            return -1
        if v1 == v2:
            return 0
        return 1

    def __cmpTupleUnlessNone (self, v1, v2):
        rv = self.__cmpSingleUnlessNone(v1.__locationBase, v2.__locationBase)
        if rv is None:
            rv = self.__cmpSingleUnlessNone(v1.__lineNumber, v2.__lineNumber)
        if rv is None:
            rv = self.__cmpSingleUnlessNone(v1.__columnNumber, v2.__columnNumber)
        return rv

    def __hash__ (self):
        return hash((self.__locationBase, self.__lineNumber, self.__columnNumber))

    def __eq__ (self, other):
        """Comparison by locationBase, then lineNumber, then columnNumber."""
        if other is None:
            return False
        rv = self.__cmpTupleUnlessNone(self, other)
        if rv is None:
            return True
        return 0 == rv

    def __lt__ (self, other):
        if other is None:
            return False
        rv = self.__cmpTupleUnlessNone(self, other)
        if rv is None:
            return False
        return -1 == rv

    def __str__ (self):
        if self.locationBase is None:
            lb = '<unknown>'
        else:
            # No, this should not be os.sep.  The location is
            # expected to be a URI.
            lb = self.locationBase.rsplit('/', 1)[-1]
        return '%s[%s:%s]' % (lb, self.lineNumber, self.columnNumber)

    def __repr__ (self):
        t = type(self)
        ctor = '%s.%s' % (t.__module__, t.__name__)
        return '%s(%s, %r, %r)' % (ctor, repr2to3(self.__locationBase), self.__lineNumber, self.__columnNumber)

class Locatable_mixin (pyxb.cscRoot):
    __location = None

    def __init__ (self, *args, **kw):
        self.__location = kw.pop('location', None)
        super(Locatable_mixin, self).__init__(*args, **kw)

    def _setLocation (self, location):
        self.__location = location

    def _location (self):
        return self.__location

def repr2to3 (v):
    """Filtered built-in repr for python 2/3 compatibility in
    generated bindings.

    All generated string values are to be unicode.  We always import
    unicode_literals from __future__, so we want plain quotes with no
    prefix u.  Strip that off.

    Integer constants should not have the suffix L even if they do not
    fit in a Python2 int.  The references generated through this
    function are never used for calculations, so the implicit cast to
    a larger type is sufficient.

    All other values use their standard representations.
    """
    if isinstance(v, six.string_types):
        qu = QuotedEscaped(v)
        if 'u' == qu[0]:
            return qu[1:]
        return qu
    if isinstance(v, six.integer_types):
        vs = repr(v)
        if vs.endswith('L'):
            return vs[:-1]
        return vs
    return repr(v)
