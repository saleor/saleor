from saleor.graphql.api import Query, Mutation
from saleor.graphql.core.enums import unit_enums
from saleor.graphql.core.federation import build_federated_schema


class Query(
    Query
):
    pass


class Mutation(
    Mutation
):
    pass


schema = build_federated_schema(Query, mutation=Mutation, types=unit_enums)
