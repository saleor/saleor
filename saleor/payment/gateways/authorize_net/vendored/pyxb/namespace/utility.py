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

"""Utility functions related to U{XML Namespaces<http://www.w3.org/TR/2006/REC-xml-names-20060816/index.html>}."""

import logging
import pyxb
import pyxb.namespace
from pyxb.utils import six

_log = logging.getLogger(__name__)

def NamespaceInstance (namespace):
    """Get a namespace instance for the given namespace.

    This is used when it is unclear whether the namespace is specified by URI
    or by instance or by any other mechanism we might dream up in the
    future."""
    if isinstance(namespace, pyxb.namespace.Namespace):
        return namespace
    if isinstance(namespace, six.string_types):
        return NamespaceForURI(namespace, True)
    raise pyxb.LogicError('Cannot identify namespace from value of type %s' % (type(namespace),))

def NamespaceForURI (uri, create_if_missing=False):
    """Given a URI, provide the L{Namespace} instance corresponding to it.

    This can only be used to lookup or create real namespaces.  To create
    absent namespaces, use L{CreateAbsentNamespace}.

    @param uri: The URI that identifies the namespace
    @type uri: A non-empty C{str} or C{unicode} string
    @keyword create_if_missing: If C{True}, a namespace for the given URI is
    created if one has not already been registered.  Default is C{False}.
    @type create_if_missing: C{bool}
    @return: The Namespace corresponding to C{uri}, if available
    @rtype: L{Namespace} or C{None}
    @raise pyxb.LogicError: The uri is not a non-empty string
    """
    if not isinstance(uri, six.string_types):
        raise pyxb.LogicError('Cannot lookup absent namespaces')
    if 0 == len(uri):
        raise pyxb.LogicError('Namespace URIs must not be empty strings')
    rv = pyxb.namespace.Namespace._NamespaceForURI(uri)
    if (rv is None) and create_if_missing:
        rv = pyxb.namespace.Namespace(uri)
    return rv

def CreateAbsentNamespace ():
    """Create an absent namespace.

    Use this when you need a namespace for declarations in a schema with no
    target namespace.  Absent namespaces are not stored in the infrastructure;
    it is your responsibility to hold on to the reference you get from this,
    because you won't be able to look it up."""
    return pyxb.namespace.Namespace.CreateAbsentNamespace()

def AvailableNamespaces ():
    """Return the complete set of Namespace instances known to the system."""
    return pyxb.namespace.Namespace.AvailableNamespaces()
