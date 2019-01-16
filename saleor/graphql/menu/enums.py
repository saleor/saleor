import graphene


class NavigationType(graphene.Enum):
    MAIN = 'main'
    SECONDARY = 'secondary'

    @property
    def description(self):
        if self == NavigationType.MAIN:
            return 'Main storefront\'s navigation.'
        if self == NavigationType.SECONDARY:
            return 'Secondary storefront\'s navigation.'
        raise ValueError('Unsupported enum value: %s' % self.value)
