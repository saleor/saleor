import graphene


class CategoryAncestorsCache:
    """Cache used to store ancestors of a category in GraphQL context.

    Allows to reduce the number of database queries. Categories of the same
    tree depth level have common ancestors, which allows us to cache them by
    the level.
    """

    def __init__(self, category):
        self._cache = {category.level: category.get_ancestors()}

    def get(self, category):
        if category.level not in self._cache:
            self._cache[category.level] = category.get_ancestors()
        return self._cache[category.level]


class DjangoPkInterface(graphene.Interface):
    """Exposes the Django model primary key."""

    pk = graphene.ID(description="Primary key")

    def resolve_pk(self, info):
        return self.pk
