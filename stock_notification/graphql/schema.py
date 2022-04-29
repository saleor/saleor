import graphene


class TransferStockMutations(graphene.ObjectType):
    from .mutations import CreateTransferStock
    create_transfer_stock = CreateTransferStock.Field()
