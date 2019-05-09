from .plan import Plan

class Pattern(object):
    def __init__(self, patterns):
        """Represents a join pattern over observable sequences."""

        self.patterns = patterns

    def and_(self, other):
        """Creates a pattern that matches the current plan matches and when the
        specified observable sequences has an available value.

        Keyword arguments:
        :param Observable other: Observable sequence to match in addition to the
            current pattern.
        :returns: Pattern object that matches when all observable sequences in
            the pattern have an available value.
        :rtype: Pattern
        """

        return Pattern(self.patterns + [other])

    def __and__(self, other):
        """Creates a pattern that matches the current plan matches and when the
        specified observable sequences has an available value.

        Keyword arguments:
        :param Observable other: Observable sequence to match in addition to the
            current pattern.
        :returns: Pattern object that matches when all observable sequences in
            the pattern have an available value.
        :rtype: Pattern
        """

        return self.and_(other)

    def then_do(self, selector):
        """Matches when all observable sequences in the pattern (specified using
        a chain of and operators) have an available value and projects the
        values.

        Keyword arguments:
        :param types.FunctionType selector: Selector that will be invoked with
            available values from the source sequences, in the same order of the
            sequences in the pattern.
        :returns: Plan that produces the projected values, to be fed (with other
            plans) to the when operator.
        :rtype: Plan
        """

        return Plan(self, selector)
