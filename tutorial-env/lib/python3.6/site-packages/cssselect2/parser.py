# coding: utf8
"""
    cssselect2.parser
    -----------------

    A parser for CSS selectors, based on the tinycss tokenizer.

    :copyright: (c) 2012 by Simon Sapin, 2017 by Guillaume Ayoub.
    :license: BSD, see LICENSE for more details.

"""

from __future__ import unicode_literals

from tinycss2 import parse_component_value_list

from ._compat import basestring

__all__ = ['parse']


def parse(input, namespaces=None):
    """
    :param input:
        A :term:`string`, or an iterable of :term:`component values`.
    """
    if isinstance(input, basestring):
        input = parse_component_value_list(input)
    tokens = TokenStream(input)
    namespaces = namespaces or {}
    yield parse_selector(tokens, namespaces)
    tokens.skip_whitespace_and_comment()
    while 1:
        next = tokens.next()
        if next is None:
            return
        elif next == ',':
            yield parse_selector(tokens, namespaces)
        else:
            raise SelectorError(next, 'unpexpected %s token.' % next.type)


def parse_selector(tokens, namespaces):
    result, pseudo_element = parse_compound_selector(tokens, namespaces)
    while 1:
        has_whitespace = tokens.skip_whitespace()
        while tokens.skip_comment():
            has_whitespace = tokens.skip_whitespace() or has_whitespace
        if pseudo_element is not None:
            return Selector(result, pseudo_element)
        peek = tokens.peek()
        if peek is None or peek == ',':
            return Selector(result, pseudo_element)
        elif peek in ('>', '+', '~'):
            combinator = peek.value
            tokens.next()
        elif has_whitespace:
            combinator = ' '
        else:
            return Selector(result, pseudo_element)
        compound, pseudo_element = parse_compound_selector(tokens, namespaces)
        result = CombinedSelector(result, combinator, compound)


def parse_compound_selector(tokens, namespaces):
    type_selectors = parse_type_selector(tokens, namespaces)
    simple_selectors = type_selectors if type_selectors is not None else []
    while 1:
        simple_selector, pseudo_element = parse_simple_selector(
            tokens, namespaces)
        if pseudo_element is not None or simple_selector is None:
            break
        simple_selectors.append(simple_selector)

    if (simple_selectors or type_selectors is not None or
            pseudo_element is not None):
        return CompoundSelector(simple_selectors), pseudo_element
    else:
        peek = tokens.peek()
        raise SelectorError(peek, 'expected a compound selector, got %s'
                            % (peek.type if peek else 'EOF'))


def parse_type_selector(tokens, namespaces):
    tokens.skip_whitespace()
    qualified_name = parse_qualified_name(tokens, namespaces)
    if qualified_name is None:
        return None

    simple_selectors = []
    namespace, local_name = qualified_name
    if local_name is not None:
        simple_selectors.append(LocalNameSelector(local_name))
    if namespace is not None:
        simple_selectors.append(NamespaceSelector(namespace))
    return simple_selectors


def parse_simple_selector(tokens, namespaces, in_negation=False):
    peek = tokens.peek()
    if peek is None:
        return None, None
    if peek.type == 'hash' and peek.is_identifier:
        tokens.next()
        return IDSelector(peek.value), None
    elif peek == '.':
        tokens.next()
        next = tokens.next()
        if next is None or next.type != 'ident':
            raise SelectorError(
                next, 'Expected a class name, got %s' % next)
        return ClassSelector(next.value), None
    elif peek.type == '[] block':
        tokens.next()
        attr = parse_attribute_selector(TokenStream(peek.content), namespaces)
        return attr, None
    elif peek == ':':
        tokens.next()
        next = tokens.next()
        if next == ':':
            next = tokens.next()
            if next is None or next.type != 'ident':
                raise SelectorError(
                    next, 'Expected a pseudo-element name, got %s' % next)
            return None, next.lower_value
        elif next is not None and next.type == 'ident':
            name = next.lower_value
            if name in ('before', 'after', 'first-line', 'first-letter'):
                return None, name
            else:
                return PseudoClassSelector(name), None
        elif next is not None and next.type == 'function':
            name = next.lower_name
            if name == 'not':
                if in_negation:
                    raise SelectorError(next, 'nested :not()')
                return parse_negation(next, namespaces), None
            else:
                return (
                    FunctionalPseudoClassSelector(name, next.arguments), None)
        else:
            raise SelectorError(next, 'unexpected %s token.' % next)
    else:
        return None, None


def parse_negation(negation_token, namespaces):
    tokens = TokenStream(negation_token.arguments)
    type_selectors = parse_type_selector(tokens, namespaces)
    if type_selectors is not None:
        return NegationSelector(type_selectors)

    simple_selector, pseudo_element = parse_simple_selector(
        tokens, namespaces, in_negation=True)
    tokens.skip_whitespace()
    if pseudo_element is None and tokens.next() is None:
        return NegationSelector([simple_selector])
    else:
        raise SelectorError(
            negation_token, ':not() only accepts a simple selector')


def parse_attribute_selector(tokens, namespaces):
    tokens.skip_whitespace()
    qualified_name = parse_qualified_name(
        tokens, namespaces, is_attribute=True)
    if qualified_name is None:
        next = tokens.next()
        raise SelectorError(
            next, 'expected attribute name, got %s' % next)
    namespace, local_name = qualified_name

    tokens.skip_whitespace()
    peek = tokens.peek()
    if peek is None:
        operator = None
        value = None
    elif peek in ('=', '~=', '|=', '^=', '$=', '*='):
        operator = peek.value
        tokens.next()
        tokens.skip_whitespace()
        next = tokens.next()
        if next is None or next.type not in ('ident', 'string'):
            next_type = 'None' if next is None else next.type
            raise SelectorError(
                next, 'expected attribute value, got %s' % next_type)
        value = next.value
    else:
        raise SelectorError(
            peek, 'expected attribute selector operator, got %s' % peek)

    tokens.skip_whitespace()
    next = tokens.next()
    if next is not None:
        raise SelectorError(next, 'expected ], got %s' % next.type)
    return AttributeSelector(namespace, local_name, operator, value)


def parse_qualified_name(tokens, namespaces, is_attribute=False):
    """Returns None (not a qualified name) or (ns, local),
    in which None is a wildcard. The empty string for ns is "no namespace".

    """
    peek = tokens.peek()
    if peek is None:
        return None
    if peek.type == 'ident':
        first_ident = tokens.next()
        peek = tokens.peek()
        if peek != '|':
            namespace = '' if is_attribute else namespaces.get(None, None)
            return namespace, (first_ident.value, first_ident.lower_value)
        tokens.next()
        namespace = namespaces.get(first_ident.value)
        if namespace is None:
            raise SelectorError(
                first_ident,
                'undefined namespace prefix: ' + first_ident.value)
    elif peek == '*':
        next = tokens.next()
        peek = tokens.peek()
        if peek != '|':
            if is_attribute:
                raise SelectorError(
                    next, 'Expected local name, got %s' % next.type)
            return namespaces.get(None, None), None
        tokens.next()
        namespace = None
    elif peek == '|':
        tokens.next()
        namespace = ''
    else:
        return None

    # If we get here, we just consumed '|' and set ``namespace``
    next = tokens.next()
    if next.type == 'ident':
        return namespace, (next.value, next.lower_value)
    elif next == '*' and not is_attribute:
        return namespace, None
    else:
        raise SelectorError(next, 'Expected local name, got %s' % next.type)


class SelectorError(ValueError):
    """A specialized ``ValueError`` for invalid selectors."""


class TokenStream(object):
    def __init__(self, tokens):
        self.tokens = iter(tokens)
        self.peeked = []  # In reversed order

    def next(self):
        if self.peeked:
            return self.peeked.pop()
        else:
            return next(self.tokens, None)

    def peek(self):
        if not self.peeked:
            self.peeked.append(next(self.tokens, None))
        return self.peeked[-1]

    def skip(self, skip_types):
        found = False
        while 1:
            peek = self.peek()
            if peek is None or peek.type not in skip_types:
                break
            self.next()
            found = True
        return found

    def skip_whitespace(self):
        return self.skip(['whitespace'])

    def skip_comment(self):
        return self.skip(['comment'])

    def skip_whitespace_and_comment(self):
        return self.skip(['comment', 'whitespace'])


class Selector(object):
    def __init__(self, tree, pseudo_element=None):
        self.parsed_tree = tree
        if pseudo_element is None:
            self.pseudo_element = pseudo_element
            #: Tuple of 3 integers: http://www.w3.org/TR/selectors/#specificity
            self.specificity = tree.specificity
        else:
            self.pseudo_element = pseudo_element
            a, b, c = tree.specificity
            self.specificity = a, b, c + 1

    def __repr__(self):
        if self.pseudo_element is None:
            return repr(self.parsed_tree)
        else:
            return '%r::%s' % (self.parsed_tree, self.pseudo_element)


class CombinedSelector(object):
    def __init__(self, left, combinator, right):
        #: Combined or compound selector
        self.left = left
        # One of `` `` (a single space), ``>``, ``+`` or ``~``.
        self.combinator = combinator
        #: compound selector
        self.right = right

    @property
    def specificity(self):
        a1, b1, c1 = self.left.specificity
        a2, b2, c2 = self.right.specificity
        return a1 + a2, b1 + b2, c1 + c2

    def __repr__(self):
        return '%r%s%r' % (self.left, self.combinator, self.right)


class CompoundSelector(object):
    """Aka. sequence of simple selectors, in Level 3."""
    def __init__(self, simple_selectors):
        self.simple_selectors = simple_selectors

    @property
    def specificity(self):
        if self.simple_selectors:
            # zip(*foo) turns [(a1, b1, c1), (a2, b2, c2), ...]
            # into [(a1, a2, ...), (b1, b2, ...), (c1, c2, ...)]
            return tuple(map(sum, zip(
                *(sel.specificity for sel in self.simple_selectors))))
        else:
            return 0, 0, 0

    def __repr__(self):
        return ''.join(map(repr, self.simple_selectors))


class LocalNameSelector(object):
    specificity = 0, 0, 1

    def __init__(self, local_name):
        self.local_name, self.lower_local_name = local_name

    def __repr__(self):
        return self.local_name


class NamespaceSelector(object):
    specificity = 0, 0, 0

    def __init__(self, namespace):
        #: The namespace URL as a string,
        #: or the empty string for elements not in any namespace.
        self.namespace = namespace

    def __repr__(self):
        if self.namespace == '':
            return '|'
        else:
            return '{%s}|' % self.namespace


class IDSelector(object):
    specificity = 1, 0, 0

    def __init__(self, ident):
        self.ident = ident

    def __repr__(self):
        return '#' + self.ident


class ClassSelector(object):
    specificity = 0, 1, 0

    def __init__(self, class_name):
        self.class_name = class_name

    def __repr__(self):
        return '.' + self.class_name


class AttributeSelector(object):
    specificity = 0, 1, 0

    def __init__(self, namespace, name, operator, value):
        self.namespace = namespace
        self.name, self.lower_name = name
        #: A string like ``=`` or ``~=``, or None for ``[attr]`` selectors
        self.operator = operator
        #: A string, or None for ``[attr]`` selectors
        self.value = value

    def __repr__(self):
        namespace = ('*|' if self.namespace is None
                     else '{%s}' % self.namespace)
        return '[%s%s%s%r]' % (namespace, self.name, self.operator, self.value)


class PseudoClassSelector(object):
    specificity = 0, 1, 0

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return ':' + self.name


class FunctionalPseudoClassSelector(object):
    specificity = 0, 1, 0

    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments

    def __repr__(self):
        return ':%s%r' % (self.name, tuple(self.arguments))


class NegationSelector(CompoundSelector):
    def __repr__(self):
        return ':not(%r)' % CompoundSelector.__repr__(self)
