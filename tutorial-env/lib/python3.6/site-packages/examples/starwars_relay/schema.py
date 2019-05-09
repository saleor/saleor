import graphene
from graphene import relay

from .data import create_ship, get_empire, get_faction, get_rebels, get_ship


class Ship(graphene.ObjectType):
    """A ship in the Star Wars saga"""

    class Meta:
        interfaces = (relay.Node,)

    name = graphene.String(description="The name of the ship.")

    @classmethod
    def get_node(cls, info, id):
        return get_ship(id)


class ShipConnection(relay.Connection):
    class Meta:
        node = Ship


class Faction(graphene.ObjectType):
    """A faction in the Star Wars saga"""

    class Meta:
        interfaces = (relay.Node,)

    name = graphene.String(description="The name of the faction.")
    ships = relay.ConnectionField(
        ShipConnection, description="The ships used by the faction."
    )

    def resolve_ships(self, info, **args):
        # Transform the instance ship_ids into real instances
        return [get_ship(ship_id) for ship_id in self.ships]

    @classmethod
    def get_node(cls, info, id):
        return get_faction(id)


class IntroduceShip(relay.ClientIDMutation):
    class Input:
        ship_name = graphene.String(required=True)
        faction_id = graphene.String(required=True)

    ship = graphene.Field(Ship)
    faction = graphene.Field(Faction)

    @classmethod
    def mutate_and_get_payload(
        cls, root, info, ship_name, faction_id, client_mutation_id=None
    ):
        ship = create_ship(ship_name, faction_id)
        faction = get_faction(faction_id)
        return IntroduceShip(ship=ship, faction=faction)


class Query(graphene.ObjectType):
    rebels = graphene.Field(Faction)
    empire = graphene.Field(Faction)
    node = relay.Node.Field()

    def resolve_rebels(self, info):
        return get_rebels()

    def resolve_empire(self, info):
        return get_empire()


class Mutation(graphene.ObjectType):
    introduce_ship = IntroduceShip.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
