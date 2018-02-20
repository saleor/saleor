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


def get_node(info, id, only_type=None):
    """Return node or throw an error if the node with given ID does not exist."""
    node = graphene.Node.get_node_from_global_id(info, id, only_type=only_type)
    if not node:
        raise Exception(
            "Could not resolve to a node with the global id of '%s'." % id)
    return node
