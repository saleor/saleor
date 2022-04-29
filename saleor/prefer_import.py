from saleor.graphql import api as core_api


def patch_schema():
    from graphene_federation import build_schema
    from stock_notification.graphql import schema

    class Query(
        core_api.Query,

    ):
        pass

    class Mutation(
        core_api.Mutation,
        schema.TransferStockMutations
    ):
        pass

    core_api.schema = build_schema(query=Query, mutation=Mutation)


patch_schema()
schema = core_api.schema
