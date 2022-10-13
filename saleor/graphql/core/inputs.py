import graphene


class ReorderInput(graphene.InputObjectType):
    id = graphene.ID(required=True, description="The ID of the item to move.")
    sort_order = graphene.Int(
        description=(
            "The new relative sorting position of the item (from -inf to +inf). "
            "1 moves the item one position forward, -1 moves the item one position "
            "backward, 0 leaves the item unchanged."
        )
    )
