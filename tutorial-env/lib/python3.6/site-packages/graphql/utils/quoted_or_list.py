import functools

# Necessary for static type checking
if False:  # flake8: noqa
    from typing import List


MAX_LENGTH = 5


def quoted_or_list(items):
    # type: (List[str]) -> str
    """Given [ A, B, C ] return '"A", "B" or "C"'."""
    selected = items[:MAX_LENGTH]
    quoted_items = ('"{}"'.format(t) for t in selected)

    def quoted_or_text(text, quoted_and_index):
        index = quoted_and_index[0]
        quoted_item = quoted_and_index[1]
        text += (
            (", " if len(selected) > 2 and not index == len(selected) - 1 else " ")
            + ("or " if index == len(selected) - 1 else "")
            + quoted_item
        )
        return text

    enumerated_items = enumerate(quoted_items)
    first_item = next(enumerated_items)[1]
    return functools.reduce(quoted_or_text, enumerated_items, first_item)
