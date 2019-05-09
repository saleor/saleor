import graphene


class ErrorType(graphene.ObjectType):
    field = graphene.String()
    messages = graphene.List(graphene.String)
