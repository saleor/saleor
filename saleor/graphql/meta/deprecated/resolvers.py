# Deprecated we should remove it in #5221
def resolve_private_meta(root, _info):
    return [root.private_metadata]


def resolve_meta(root, _info):
    return [root.metadata]
