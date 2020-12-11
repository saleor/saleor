import graphene

from .mutations import ReserveStock


class ReservationMutations(graphene.ObjectType):
    reserve_stock = ReserveStock.Field()
