import graphene

from .mutations import ReservationCreate


class ReservationMutations(graphene.ObjectType):
    reservation_create = ReservationCreate.Field()
