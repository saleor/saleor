from ..language.ast import Node


def ast_to_dict(node, include_loc=False):
    if isinstance(node, Node):
        d = {"kind": node.__class__.__name__}
        if hasattr(node, "_fields"):
            for field in node._fields:
                d[field] = ast_to_dict(getattr(node, field), include_loc)

        if include_loc and hasattr(node, "loc") and node.loc:
            d["loc"] = {"start": node.loc.start, "end": node.loc.end}

        return d

    elif isinstance(node, list):
        return [ast_to_dict(item, include_loc) for item in node]

    return node
