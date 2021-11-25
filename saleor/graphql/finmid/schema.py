import graphene


class FinmidQueries(graphene.ObjectType):
    ping = graphene.String()

    precheck = graphene.Boolean(amount=graphene.Float(description="Order amount.", required=True))

    def resolve_ping(self, info):
        return 'Pong!'

    def resolve_precheck(self, info, amount):
        return amount < 100.0
