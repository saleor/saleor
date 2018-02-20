import graphene


def get_node(info, id, only_type=None):
    """Return node or throw an error if the node does not exist."""
    node = graphene.Node.get_node_from_global_id(info, id, only_type=only_type)
    if not node:
        raise Exception(
            "Could not resolve to a node with the global id of '%s'." % id)
    return node
