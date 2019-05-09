import itertools

from ..language.ast import Document

# Necessary for static type checking
if False:  # flake8: noqa
    from typing import Iterable


def concat_ast(asts):
    # type: (Iterable[Document]) -> Document
    return Document(
        definitions=list(
            itertools.chain.from_iterable(document.definitions for document in asts)
        )
    )
