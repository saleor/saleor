from operator import itemgetter


def resolve_private_meta(root, _info):
    return sorted(
        [
            {"namespace": namespace, "metadata": data}
            for namespace, data in root.private_meta.items()
        ],
        key=itemgetter("namespace"),
    )


def resolve_meta(root, _info):
    return sorted(
        [
            {"namespace": namespace, "metadata": data}
            for namespace, data in root.meta.items()
        ],
        key=itemgetter("namespace"),
    )
