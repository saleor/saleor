from ...language.visitor import Visitor

# Necessary for static type checking
if False:  # flake8: noqa
    from ..validation import ValidationContext


class ValidationRule(Visitor):
    __slots__ = ("context",)

    def __init__(self, context):
        # type: (ValidationContext) -> None
        self.context = context
