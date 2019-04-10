import django_filters


class EnumFilter(django_filters.CharFilter):
    """
    Filter for GraphQL's enum objects. enum_class stores graphQL enum
    needed to generated schema. method needs to be always pass explicitly"""
    def __init__(self, enum_class, *args, **kwargs):
        assert kwargs.get('method'), ("Providing exact filter method is "
                                      "required for EnumFilter")
        self.enum_class = enum_class
        super().__init__(*args, **kwargs)
