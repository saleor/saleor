from ..utils import from_global_id_or_error


def resolve_federation_references(graphql_type, roots, queryset):
    ids = [
        from_global_id_or_error(root.id, graphql_type, raise_error=True)[1]
        for root in roots
    ]
    objects = {str(obj.id): obj for obj in queryset.filter(id__in=ids)}
    return [objects.get(root_id) for root_id in ids]
