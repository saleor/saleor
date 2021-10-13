from .filterset import setup_filterset


def get_filterset_class(filterset_class):
    """
    Get the class to be used as the FilterSet.
    """
    graphene_filterset_class = setup_filterset(filterset_class)
    replace_csv_filters(graphene_filterset_class)
    return graphene_filterset_class


def replace_csv_filters(filterset_class):
    """
    Replace the "in" and "range" filters (that are not explicitly declared)
    to not be BaseCSVFilter (BaseInFilter, BaseRangeFilter) objects anymore
    but our custom InFilter/RangeFilter filter class that use the input
    value as filter argument on the queryset.
    This is because those BaseCSVFilter are expecting a string as input with
    comma separated values.
    But with GraphQl we can actually have a list as input and have a proper
    type verification of each value in the list.
    See issue https://github.com/graphql-python/graphene-django/issues/1068.
    """
    for name, filter_field in list(filterset_class.base_filters.items()):
        # Do not touch any declared filters
        if name in filterset_class.declared_filters:
            continue

        filter_type = filter_field.lookup_expr
        if filter_type == "in":
            filterset_class.base_filters[name] = ListFilter(
                field_name=filter_field.field_name,
                lookup_expr=filter_field.lookup_expr,
                label=filter_field.label,
                method=filter_field.method,
                exclude=filter_field.exclude,
                **filter_field.extra
            )
        elif filter_type == "range":
            filterset_class.base_filters[name] = RangeFilter(
                field_name=filter_field.field_name,
                lookup_expr=filter_field.lookup_expr,
                label=filter_field.label,
                method=filter_field.method,
                exclude=filter_field.exclude,
                **filter_field.extra
            )
