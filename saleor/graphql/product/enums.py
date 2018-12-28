import graphene


class AttributeTypeEnum(graphene.Enum):
    PRODUCT = 'PRODUCT'
    VARIANT = 'VARIANT'


class AttributeValueType(graphene.Enum):
    COLOR = 'COLOR'
    GRADIENT = 'GRADIENT'
    URL = 'URL'
    STRING = 'STRING'


class StockAvailability(graphene.Enum):
    IN_STOCK = 'AVAILABLE'
    OUT_OF_STOCK = 'OUT_OF_STOCK'


class ProductOrderField(graphene.Enum):
    NAME = 'name'
    PRICE = 'price'
    DATE = 'updated_at'

    @property
    def description(self):
        if self == ProductOrderField.NAME:
            return 'Sort products by name.'

        if self == ProductOrderField.PRICE:
            return 'Sort products by price.'

        if self == ProductOrderField.DATE:
            return 'Sort products by update date.'


class OrderDirection(graphene.Enum):
    ASC = ''
    DESC = '-'

    @property
    def description(self):
        if self == OrderDirection.ASC:
            return 'Specifies an ascending sort order.'
        else:
            return 'Specifies a descending sort order.'
