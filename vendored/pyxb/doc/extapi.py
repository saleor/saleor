# Kenozooid - software stack to support different capabilities of dive
# computers.
#
# Copyright (C) 2009 by Artur Wroblewski &lt;wrobell@pld-linux.org&gt;
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see &lt;http://www.gnu.org/licenses/&gt;.
#
# Modifications by PAB to override reference text

from __future__ import print_function
import os.path
from docutils import nodes
import sys
import re

__Reference_re = re.compile('\s*(.*)\s+<(.*)>\s*$', re.MULTILINE + re.DOTALL)

def api_role(role, rawtext, text, lineno, inliner, options={}, content=[]):
    """
    Role `:api:` bridges generated API documentation by tool like EpyDoc
    with Sphinx Python Documentation Generator.

    Other tools, other than EpyDoc, can be easily supported as well.

    First generate the documentation to be referenced, i.e. with EpyDoc::

        $ mkdir -p doc/html/api
        $ epydoc -o doc/html/api ...

    Next step is to generate documentation with Sphinx::

        $ sphinx-build doc doc/html

    """
    basedir = 'api'
    prefix = 'html/' # fixme: fetch it from configuration
    exists = lambda f: os.path.exists(prefix + f)

    # assume module is references

    #print 'Text "%s"' % (text,)
    mo = __Reference_re.match(text)
    label = None
    if mo is not None:
        ( label, text ) = mo.group(1, 2)
    name = text.strip()

    uri = file = '%s/%s-module.html' % (basedir, text)
    chunks = text.split('.')

    #print 'Trying module file %s' % (file,)

    # if not module, then a class
    if not exists(file):
        name = text.split('.')[-1]
        uri = file = '%s/%s-class.html' % (basedir, text)
    #print 'Trying class file %s' % (file,)

    # if not a class, then function or class method
    if not exists(file):
        method = chunks[-1]
        fprefix = '.'.join(chunks[:-1])
        # assume function is referenced
        file = '%s/%s-module.html' % (basedir, fprefix)
        #print 'Trying method file %s' % (file,)
        if exists(file):
            uri = '%s#%s' % (file, method)
        else:
            # class method is references
            file = '%s/%s-class.html' % (basedir, fprefix)
            if exists(file):
                name = '.'.join(chunks[-2:]) # name should be Class.method
                uri = '%s/%s-class.html#%s' % (basedir, fprefix, method)

    if label is None:
        label = name
    if exists(file):
        node = nodes.reference(rawtext, label, refuri=uri, **options)
    else:
        # cannot find reference, then just inline the text
        print('WARNING: Unable to find %s in API' % (text,))
        node = nodes.literal(rawtext, text)

    return [node], []

def ticket_role(role, rawtext, text, lineno, inliner, options={}, content=[]):
    """
    Role `:ticket:` generates references to SourceForge tickets.
    """
    trac_root = 'https://sourceforge.net/p/pyxb/tickets'

    # assume module is references

    #print 'Text "%s"' % (text,)
    mo = __Reference_re.match(text)
    label = None
    if mo is not None:
        ( label, text ) = mo.group(1, 2)
    ticket = text.strip()

    uri = '%s/%s/' % (trac_root, ticket)
    if label is None:
        label = 'SF ticket %s' % (ticket,)
    node = nodes.reference(rawtext, label, refuri=uri, **options)

    return [node], []

def issue_role(role, rawtext, text, lineno, inliner, options={}, content=[]):
    """
    Role `:issue:` generates references to github issues.
    """
    issue_root = 'https://github.com/pabigot/pyxb/issues'

    # assume module is references

    mo = __Reference_re.match(text)
    label = None
    if mo is not None:
        ( label, text ) = mo.group(1, 2)
    ticket = text.strip()

    uri = '%s/%s/' % (issue_root, ticket)
    if label is None:
        label = 'issue %s' % (ticket,)
    node = nodes.reference(rawtext, label, refuri=uri, **options)

    return [node], []


def pyex_role(role, rawtext, text, lineno, inliner, options={}, content=[]):
    """
    Role `:pyex:` generates reference to Python exception classes.
    """

    pyex_fmt = 'http://docs.python.org/library/exceptions.html#exceptions.%s'
    mo = __Reference_re.match(text)
    label = None
    if mo is not None:
        ( label, text ) = mo.group(1, 2)
    exc = text.strip()
    print('Python exception %s as %s' % (text, label))

    uri = pyex_fmt % (exc,)
    if label is None:
        label = '%s' % (exc,)
    node = nodes.reference(rawtext, label, refuri=uri, **options)

    return [node], []

def setup(app):
    app.add_role('api', api_role)
    app.add_config_value('epydoc_basedir', 'api', False)
    app.add_config_value('epydoc_prefix', 'doc/html/', False)
    app.add_role('ticket', ticket_role)
    app.add_role('issue', issue_role)
    app.add_role('pyex', pyex_role)
