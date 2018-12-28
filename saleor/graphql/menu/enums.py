import graphene


class NavigationType(graphene.Enum):
    MAIN = 'main'
    SECONDARY = 'secondary'

    @property
    def description(self):
        if self == NavigationType.MAIN:
            return 'Main storefront\'s navigation.'
        return 'Secondary storefront\'s navigation.'
