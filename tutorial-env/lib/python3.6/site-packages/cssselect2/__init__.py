# coding: utf8
"""
    cssselect2
    ----------

    CSS selectors for ElementTree.

    :copyright: (c) 2012 by Simon Sapin, 2017 by Guillaume Ayoub.
    :license: BSD, see LICENSE for more details.

"""

from __future__ import unicode_literals

import operator

from webencodings import ascii_lower

# Classes are imported here to expose them at the top level of the module
from .compiler import compile_selector_list  # noqa
from .parser import SelectorError  # noqa
from .tree import ElementWrapper  # noqa


VERSION = '0.2.1'


class Matcher(object):
    """A CSS selectors storage that can match against HTML elements."""
    def __init__(self):
        self.id_selectors = {}
        self.class_selectors = {}
        self.lower_local_name_selectors = {}
        self.namespace_selectors = {}
        self.other_selectors = []
        self.order = 0

    def add_selector(self, selector, payload):
        """
        Add a selector and its payload to the matcher.

        :param selector:
            A :class:`CompiledSelector` object.
        :param payload:
            Some data associated to the selector,
            such as :class:`declarations <~tinycss2.ast.Declaration>`
            parsed from the :attr:`~tinycss2.ast.QualifiedRule.content`
            of a style rule.
            It can be any Python object,
            and will be returned as-is by :meth:`match`.

        """
        self.order += 1

        if selector.never_matches:
            return

        entry = (
            selector.test, selector.specificity, self.order,
            selector.pseudo_element, payload)
        if selector.id is not None:
            self.id_selectors.setdefault(selector.id, []).append(entry)
        elif selector.class_name is not None:
            self.class_selectors.setdefault(selector.class_name, []) \
                .append(entry)
        elif selector.local_name is not None:
            self.lower_local_name_selectors.setdefault(
                selector.lower_local_name, []).append(entry)
        elif selector.namespace is not None:
            self.namespace_selectors.setdefault(selector.namespace, []) \
                .append(entry)
        else:
            self.other_selectors.append(entry)

    def match(self, element):
        """
        Match selectors against the given element.

        :param element:
            An :class:`ElementWrapper`.
        :returns:
            A list of the :obj:`payload` objects associated
            to selectors that match element,
            in order of lowest to highest :attr:`~CompiledSelector.specificity`
            and in order of addition with :meth:`add_selector`
            among selectors of equal specificity.

        """
        relevant_selectors = []

        if element.id is not None:
            relevant_selectors.append(self.id_selectors.get(element.id, []))

        for class_name in element.classes:
            relevant_selectors.append(self.class_selectors.get(class_name, []))

        relevant_selectors.append(
            self.lower_local_name_selectors.get(
                ascii_lower(element.local_name), []))
        relevant_selectors.append(
            self.namespace_selectors.get(element.namespace_url, []))
        relevant_selectors.append(self.other_selectors)

        results = [
            (specificity, order, pseudo, payload)
            for selector_list in relevant_selectors
            for test, specificity, order, pseudo, payload in selector_list
            if test(element)
        ]
        results.sort(key=SORT_KEY)
        return results


SORT_KEY = operator.itemgetter(0, 1)
