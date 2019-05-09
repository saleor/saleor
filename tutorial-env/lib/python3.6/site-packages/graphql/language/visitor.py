from copy import copy

import six

from . import ast
from .visitor_meta import QUERY_DOCUMENT_KEYS, VisitorMeta

# Necessary for static type checking
if False:  # flake8: noqa
    from typing import Any, List, Optional, Union, Tuple, Dict
    from ..utils.type_info import TypeInfo
    from ..validation.validation import UsageVisitor
    from .ast import Node, Document, OperationDefinition
    from .printer import PrintingVisitor


class _Falsey(object):
    def __nonzero__(self):
        return False

    def __bool__(self):
        # type: () -> bool
        return False


class _Break(object):
    pass


BREAK = _Break()
REMOVE = _Falsey()


class Stack(object):
    __slots__ = "in_array", "index", "keys", "edits", "prev"

    def __init__(self, in_array, index, keys, edits, prev):
        # type: (bool, int, Any, List[Tuple[Union[str, int], Any]], Optional[Stack]) -> None
        self.in_array = in_array
        self.index = index
        self.keys = keys
        self.edits = edits
        self.prev = prev


def visit(root, visitor, key_map=None):
    # type: (Union[Node, List[Node]], Visitor, Optional[Dict[Node, Tuple]]) -> Any
    visitor_keys = key_map or QUERY_DOCUMENT_KEYS

    stack = None  # type: Optional[Stack]
    in_array = isinstance(root, list)
    keys = [root]
    index = -1
    edits = []  # type: List[Tuple[Union[str, int], Any]]
    parent = None  # type: Optional[Node]
    path = []  # type: List
    ancestors = []  # type: List[Node]
    new_root = root
    leave = visitor.leave
    enter = visitor.enter
    path_pop = path.pop
    ancestors_pop = ancestors.pop
    path_append = path.append
    ancestors_append = ancestors.append

    while True:
        index += 1
        is_leaving = index == len(keys)
        is_edited = is_leaving and edits
        if is_leaving:
            key = path_pop() if ancestors else None
            node = parent
            parent = ancestors_pop() if ancestors else None

            if is_edited:
                if in_array:
                    node = list(node)  # type: ignore
                else:
                    node = copy(node)
                edit_offset = 0
                for edit_key, edit_value in edits:
                    if in_array:
                        edit_key -= edit_offset  # type: ignore

                    if in_array and edit_value is REMOVE:
                        node.pop(edit_key)  # type: ignore
                        edit_offset += 1

                    else:
                        if isinstance(node, list):
                            node[edit_key] = edit_value
                        else:
                            setattr(node, edit_key, edit_value)  # type: ignore

            index = stack.index  # type: ignore
            keys = stack.keys  # type: ignore
            edits = stack.edits  # type: ignore
            in_array = stack.in_array  # type: ignore
            stack = stack.prev  # type: ignore

        else:
            if parent:
                key = index if in_array else keys[index]
                if isinstance(parent, list):
                    node = parent[key]
                else:
                    node = getattr(parent, key, None)

            else:
                key = None
                node = new_root  # type: ignore

            if node is REMOVE or node is None:
                continue

            if parent:
                path_append(key)

        result = None

        if not isinstance(node, list):
            assert isinstance(node, ast.Node), "Invalid AST Node: " + repr(node)

            if is_leaving:
                result = leave(node, key, parent, path, ancestors)

            else:
                result = enter(node, key, parent, path, ancestors)

            if result is BREAK:
                break

            if result is False:
                if not is_leaving:
                    path_pop()
                    continue

            elif result is not None:
                edits.append((key, result))
                if not is_leaving:
                    if isinstance(result, ast.Node):
                        node = result

                    else:
                        path_pop()
                        continue

        if result is None and is_edited:
            edits.append((key, node))

        if not is_leaving:
            stack = Stack(in_array, index, keys, edits, stack)
            in_array = isinstance(node, list)
            keys = (  # type: ignore
                node
                if in_array
                else visitor_keys.get(type(node), None) or []  # type: ignore
            )
            index = -1
            edits = []

            if parent:
                ancestors_append(parent)

            parent = node

        if not stack:
            break

    if edits:
        new_root = edits[-1][1]

    return new_root


@six.add_metaclass(VisitorMeta)
class Visitor(object):
    __slots__ = ()

    def enter(
        self,
        node,  # type: Any
        key,  # type: Union[None, int, str]
        parent,  # type: Any
        path,  # type: List[Union[int, str]]
        ancestors,  # type: List[Any]
    ):
        # type: (...) -> Any
        method = self._get_enter_handler(type(node))  # type: ignore
        if method:
            return method(self, node, key, parent, path, ancestors)
        return None

    def leave(
        self,
        node,  # type: Any
        key,  # type: Union[None, int, str]
        parent,  # type: Any
        path,  # type: List[Union[int, str]]
        ancestors,  # type: List[Any]
    ):
        # type: (...) -> Any
        method = self._get_leave_handler(type(node))  # type: ignore
        if method:
            return method(self, node, key, parent, path, ancestors)
        return None


class ParallelVisitor(Visitor):
    __slots__ = "skipping", "visitors"

    def __init__(self, visitors):
        # type: (List[Any]) -> None
        self.visitors = visitors
        self.skipping = [None] * len(
            visitors
        )  # type: List[Union[Node, _Break, _Falsey, None]]
        return None

    def enter(
        self,
        node,  # type: Any
        key,  # type: Union[None, int, str]
        parent,  # type: Any
        path,  # type: List[Union[int, str]]
        ancestors,  # type: List[Any]
    ):
        # type: (...) -> Any
        for i, visitor in enumerate(self.visitors):
            if not self.skipping[i]:
                result = visitor.enter(node, key, parent, path, ancestors)
                if result is False:
                    self.skipping[i] = node
                elif result is BREAK:
                    self.skipping[i] = BREAK
                elif result is not None:
                    return result
        return None

    def leave(
        self,
        node,  # type: Any
        key,  # type: Union[None, int, str]
        parent,  # type: Any
        path,  # type: List[Union[int, str]]
        ancestors,  # type: List[Any]
    ):
        # type: (...) -> Any
        for i, visitor in enumerate(self.visitors):
            if not self.skipping[i]:
                result = visitor.leave(node, key, parent, path, ancestors)
                if result is BREAK:
                    self.skipping[i] = BREAK
                elif result is not None and result is not False:
                    return result
            elif self.skipping[i] == node:
                self.skipping[i] = REMOVE
        return None


class TypeInfoVisitor(Visitor):
    __slots__ = "visitor", "type_info"

    def __init__(self, type_info, visitor):
        # type: (TypeInfo, Visitor) -> None
        self.type_info = type_info
        self.visitor = visitor

    def enter(
        self,
        node,  # type: Any
        key,  # type: Union[None, int, str]
        parent,  # type: Any
        path,  # type: List[Union[int, str]]
        ancestors,  # type: List[Any]
    ):
        # type: (...) -> Optional[Any]
        self.type_info.enter(node)
        result = self.visitor.enter(node, key, parent, path, ancestors)
        if result is not None:
            self.type_info.leave(node)
            if isinstance(result, ast.Node):
                self.type_info.enter(result)
        return result

    def leave(
        self,
        node,  # type: Any
        key,  # type: Union[None, int, str]
        parent,  # type: Any
        path,  # type: List[Union[int, str]]
        ancestors,  # type: List[Any]
    ):
        # type: (...) -> Optional[Any]
        result = self.visitor.leave(node, key, parent, path, ancestors)
        self.type_info.leave(node)
        return result
