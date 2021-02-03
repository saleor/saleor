import graphene

from .mutations import ReservationCreate, ReservationsRemove


class ReservationMutations(graphene.ObjectType):
    reservation_create = ReservationCreate.Field()
    reservations_remove = ReservationsRemove.Field()
