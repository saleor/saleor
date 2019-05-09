class Search:
    """
    Collection of classes used to build search queries.

    Each Builder class defines one or more methods that returns a Node
    object with the name of the field, the comparator, and the value.
    """
    class IsNodeBuilder(object):
        """Builds a query for value equality."""
        def __init__(self, name):
            self.name = name

        def __eq__(self, value):
            return self.is_equal(value)

        def is_equal(self, value):
            return Search.Node(self.name, {"is": value})

    class EqualityNodeBuilder(IsNodeBuilder):
        """Builds a query for value inequality."""
        def __ne__(self, value):
            return self.is_not_equal(value)

        def is_not_equal(self, value):
            return Search.Node(self.name, {"is_not": value})

    class KeyValueNodeBuilder(object):
        """Builds a query based on a key-value map."""
        def __init__(self, name):
            self.name = name

        def __eq__(self, value):
            return self.is_equal(value)

        def is_equal(self, value):
            return Search.Node(self.name, value)

        def __ne__(self, value):
            return self.is_not_equal(value)

        def is_not_equal(self, value):
            return Search.Node(self.name, not value)

    class PartialMatchNodeBuilder(EqualityNodeBuilder):
        """Builds a query for matching parts of a sequence."""
        def starts_with(self, value):
            return Search.Node(self.name, {"starts_with": value})

        def ends_with(self, value):
            return Search.Node(self.name, {"ends_with": value})

    class EndsWithNodeBuilder(object):
        def __init__(self, name):
            self.name = name

        def ends_with(self, value):
            return Search.Node(self.name, {"ends_with": value})

    class TextNodeBuilder(PartialMatchNodeBuilder):
        """Builds a query for matching any part of a sequence."""
        def contains(self, value):
            return Search.Node(self.name, {"contains": value})

    class Node(object):
        """Container for part of a search query."""
        def __init__(self, name, dict):
            self.name = name
            self.dict = dict

        def to_param(self):
            return self.dict

    class MultipleValueNodeBuilder(object):
        """Builds a query to check membership in a sequence."""
        def __init__(self, name, whitelist = []):
            self.name = name
            self.whitelist = whitelist

        def in_list(self, *values):
            if isinstance(values[0], list):
                values = values[0]

            invalid_args = set(values) - set(self.whitelist)
            if len(self.whitelist) > 0 and len(invalid_args) > 0:
                error_string = "Invalid argument(s) for %s: %s" % (self.name, ", ".join(invalid_args))
                raise AttributeError(error_string)
            return Search.Node(self.name, list(values))

        def __eq__(self, value):
            return self.in_list([value])

    class MultipleValueOrTextNodeBuilder(TextNodeBuilder, MultipleValueNodeBuilder):
        """Builder node supporting contains and in_list."""
        def __init__(self, name, whitelist = []):
            Search.MultipleValueNodeBuilder.__init__(self, name, whitelist)

    class RangeNodeBuilder(object):
        """Builds a query supporting <=, >=, or == value."""
        def __init__(self, name):
            self.name = name

        def __eq__(self, value):
            return self.is_equal(value)

        def is_equal(self, value):
            return Search.EqualityNodeBuilder(self.name) == value

        def __ge__(self, min):
            return self.greater_than_or_equal_to(min)

        def greater_than_or_equal_to(self, min):
            return Search.Node(self.name, {"min": min})

        def __le__(self, max):
            return self.less_than_or_equal_to(max)

        def less_than_or_equal_to(self, max):
            return Search.Node(self.name, {"max": max})

        def between(self, min, max):
            return Search.Node(self.name, {"min": min, "max": max})
