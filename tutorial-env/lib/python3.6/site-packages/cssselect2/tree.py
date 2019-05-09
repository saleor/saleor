# coding: utf8

from __future__ import unicode_literals

import xml.etree.ElementTree as etree

from webencodings import ascii_lower

from ._compat import basestring, ifilter
from .compiler import compile_selector_list, split_whitespace


class cached_property(object):
    # Borrowed from Werkzeug
    # https://github.com/mitsuhiko/werkzeug/blob/master/werkzeug/utils.py

    def __init__(self, func, name=None, doc=None):
        self.__name__ = name or func.__name__
        self.__module__ = func.__module__
        self.__doc__ = doc or func.__doc__
        self.func = func

    def __get__(self, obj, type=None, __missing=object()):
        if obj is None:
            return self
        value = obj.__dict__.get(self.__name__, __missing)
        if value is __missing:
            value = self.func(obj)
            obj.__dict__[self.__name__] = value
        return value


class ElementWrapper(object):
    """
    A wrapper for an ElementTree :class:`~xml.etree.ElementTree.Element`
    for Selector matching.

    This class should not be instanciated directly.
    :meth:`from_xml_root` or :meth:`from_html_root` should be used
    for the root element of a document,
    and other elements should be accessed (and wrappers generated)
    using methods such as :meth:`iter_children` and :meth:`iter_subtree`.

    :class:`ElementWrapper` objects compare equal
    if their underlying :class:`~xml.etree.ElementTree.Element` do.

    """
    @classmethod
    def from_xml_root(cls, root, content_language=None):
        """Wrap for selector matching the root of an XML or XHTML document.

        :param root:
            An ElementTree :class:`~xml.etree.ElementTree.Element`
            for the root element of a document.
            If the given element is not the root,
            selector matching will behave is if it were.
            In other words, selectors will be `scope-contained`_
            to the subtree rooted at that element.
        :returns:
            A new :class:`ElementWrapper`

        .. _scope-contained:
            http://dev.w3.org/csswg/selectors4/#scope-contained-selectors

        """
        return cls._from_root(root, content_language, in_html_document=False)

    @classmethod
    def from_html_root(cls, root, content_language=None):
        """Same as :meth:`from_xml_root`,
        but for documents parsed with an HTML parser
        like `html5lib <http://html5lib.readthedocs.org/>`_,
        which should be the case of documents with the ``text/html`` MIME type.

        Compared to :meth:`from_xml_root`,
        this makes element attribute names in Selectors case-insensitive.

        """
        return cls._from_root(root, content_language, in_html_document=True)

    @classmethod
    def _from_root(cls, root, content_language, in_html_document=True):
        if hasattr(root, 'getroot'):
            root = root.getroot()
        return cls(root, parent=None, index=0, previous=None,
                   in_html_document=in_html_document,
                   content_language=content_language)

    def __init__(self, etree_element, parent, index, previous,
                 in_html_document, content_language=None):
        #: The underlying ElementTree :class:`~xml.etree.ElementTree.Element`
        self.etree_element = etree_element
        #: The parent :class:`ElementWrapper`,
        #: or :obj:`None` for the root element.
        self.parent = parent
        #: The previous sibling :class:`ElementWrapper`,
        #: or :obj:`None` for the root element.
        self.previous = previous
        if parent is not None:
            #: The :attr:`parent`’s children
            #: as a list of
            #: ElementTree :class:`~xml.etree.ElementTree.Element`s.
            #: For the root (which has no parent)
            self.etree_siblings = parent.etree_children
        else:
            self.etree_siblings = [etree_element]
        #: The position within the :attr:`parent`’s children, counting from 0.
        #: ``e.etree_siblings[e.index]`` is always ``e.etree_element``.
        self.index = index
        self.in_html_document = in_html_document
        self.transport_content_language = content_language

    def __eq__(self, other):
        return (type(self) == type(other) and
                self.etree_element == other.etree_element)

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash((type(self), self.etree_element))

    def __iter__(self):
        for element in self.iter_children():
            yield element

    def iter_ancestors(self):
        """Return an iterator of existing :class:`ElementWrapper` objects
        for this element’s ancestors,
        in reversed tree order (from :attr:`parent` to the root)

        The element itself is not included,
        this is an empty sequence for the root element.

        """
        element = self
        while element.parent is not None:
            element = element.parent
            yield element

    def iter_previous_siblings(self):
        """Return an iterator of existing :class:`ElementWrapper` objects
        for this element’s previous siblings,
        in reversed tree order.

        The element itself is not included,
        this is an empty sequence for a first child or the root element.

        """
        element = self
        while element.previous is not None:
            element = element.previous
            yield element

    def iter_children(self):
        """Return an iterator of newly-created :class:`ElementWrapper` objects
        for this element’s child elements,
        in tree order.

        """
        child = None
        for i, etree_child in enumerate(self.etree_children):
            child = type(self)(
                etree_child,
                parent=self,
                index=i,
                previous=child,
                in_html_document=self.in_html_document,
            )
            yield child

    def iter_subtree(self):
        """Return an iterator of newly-created :class:`ElementWrapper` objects
        for the entire subtree rooted at this element,
        in tree order.

        Unlike in other methods, the element itself *is* included.

        This loops over an entire document:

        .. code-block:: python

            for element in ElementWrapper.from_root(root_etree).iter_subtree():
                ...

        """
        stack = [iter([self])]
        while stack:
            element = next(stack[-1], None)
            if element is None:
                stack.pop()
            else:
                yield element
                stack.append(element.iter_children())

    @staticmethod
    def _compile(selectors):
        return [
            compiled_selector.test
            for selector in selectors
            for compiled_selector in (
                [selector] if hasattr(selector, 'test')
                else compile_selector_list(selector)
            )
            if compiled_selector.pseudo_element is None and
            not compiled_selector.never_matches
        ]

    def matches(self, *selectors):
        """Return wether this elememt matches any of the given selectors.

        :param selectors:
            Each given selector is either a :class:`CompiledSelector`,
            or an argument to :func:`compile_selector_list`.

        """
        return any(test(self) for test in self._compile(selectors))

    def query_all(self, *selectors):
        """
        Return elements, in tree order, that match any of the given selectors.

        Selectors are `scope-filtered`_ to the subtree rooted at this element.

        .. _scope-filtered: http://dev.w3.org/csswg/selectors4/#scope-filtered

        :param selectors:
            Each given selector is either a :class:`CompiledSelector`,
            or an argument to :func:`compile_selector_list`.
        :returns:
            An iterator of newly-created :class:`ElementWrapper` objects.

        """
        tests = self._compile(selectors)
        if len(tests) == 1:
            return ifilter(tests[0], self.iter_subtree())
        elif selectors:
            return (
                element
                for element in self.iter_subtree()
                if any(test(element) for test in tests)
            )
        else:
            return iter(())

    def query(self, *selectors):
        """Return the first element (in tree order)
        that matches any of the given selectors.

        :param selectors:
            Each given selector is either a :class:`CompiledSelector`,
            or an argument to :func:`compile_selector_list`.
        :returns:
            A newly-created :class:`ElementWrapper` object,
            or :obj:`None` if there is no match.

        """
        return next(self.query_all(*selectors), None)

    @cached_property
    def etree_children(self):
        """This element’s children,
        as a list of ElementTree :class:`~xml.etree.ElementTree.Element`.

        Other ElementTree nodes such as
        :class:`comments <~xml.etree.ElementTree.Comment>` and
        :class:`processing instructions
        <~xml.etree.ElementTree.ProcessingInstruction>`
        are not included.

        """
        return [c for c in self.etree_element if isinstance(c.tag, basestring)]

    @cached_property
    def local_name(self):
        """The local name of this element, as a string."""
        namespace_url, local_name = _split_etree_tag(self.etree_element.tag)
        self.__dict__[str('namespace_url')] = namespace_url
        return local_name

    @cached_property
    def namespace_url(self):
        """The namespace URL of this element, as a string."""
        namespace_url, local_name = _split_etree_tag(self.etree_element.tag)
        self.__dict__[str('local_name')] = local_name
        return namespace_url

    @cached_property
    def id(self):
        """The ID of this element, as a string."""
        return self.etree_element.get('id')

    @cached_property
    def classes(self):
        """The classes of this element, as a :class:`set` of strings."""
        return set(split_whitespace(self.etree_element.get('class', '')))

    @cached_property
    def lang(self):
        """The language of this element, as a string."""
        # http://whatwg.org/C#language
        xml_lang = self.etree_element.get(
            '{http://www.w3.org/XML/1998/namespace}lang')
        if xml_lang is not None:
            return ascii_lower(xml_lang)
        is_html = (
            self.in_html_document or
            self.namespace_url == 'http://www.w3.org/1999/xhtml')
        if is_html:
            lang = self.etree_element.get('lang')
            if lang is not None:
                return ascii_lower(lang)
        if self.parent is not None:
            return self.parent.lang
        # Root elememnt
        if is_html:
            content_language = None
            for meta in etree_iter(self.etree_element,
                                   '{http://www.w3.org/1999/xhtml}meta'):
                http_equiv = meta.get('http-equiv', '')
                if ascii_lower(http_equiv) == 'content-language':
                    content_language = _parse_content_language(
                        meta.get('content'))
            if content_language is not None:
                return ascii_lower(content_language)
        # Empty string means unknown
        return _parse_content_language(self.transport_content_language) or ''

    @cached_property
    def in_disabled_fieldset(self):
        if self.parent is None:
            return False
        if (self.parent.etree_element.tag == (
                '{http://www.w3.org/1999/xhtml}fieldset') and
            self.parent.etree_element.get('disabled') is not None and (
                self.etree_element.tag != (
                    '{http://www.w3.org/1999/xhtml}legend') or
                any(s.etree_element.tag == (
                    '{http://www.w3.org/1999/xhtml}legend')
                    for s in self.iter_previous_siblings()))):
            return True
        return self.parent.in_disabled_fieldset


def _split_etree_tag(tag):
    pos = tag.rfind('}')
    if pos == -1:
        return '', tag
    else:
        assert tag[0] == '{'
        return tag[1:pos], tag[pos + 1:]


if hasattr(etree.Element, 'iter'):
    def etree_iter(element, tag=None):
        return element.iter(tag)
else:
    def etree_iter(element, tag=None):
        return element.getiterator(tag)


def _parse_content_language(value):
    if value is not None and ',' not in value:
        parts = split_whitespace(value)
        if len(parts) == 1:
            return parts[0]
