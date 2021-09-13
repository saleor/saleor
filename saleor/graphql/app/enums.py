from ...app.types import AppExtensionTarget, AppExtensionType, AppExtensionView, AppType
from ..core.enums import to_enum


def description(enum):
    if enum is None:
        return "Enum determining type of your App."
    elif enum == AppTypeEnum.LOCAL:
        return (
            "Local Saleor App. The app is fully manageable from dashboard. "
            "You can change assigned permissions, add webhooks, "
            "or authentication token"
        )
    elif enum == AppTypeEnum.THIRDPARTY:
        return (
            "Third party external App. Installation is fully automated. "
            "Saleor uses a defined App manifest to gather all required information."
        )
    return None


AppTypeEnum = to_enum(AppType, description=description)

AppExtensionTypeEnum = to_enum(AppExtensionType, description=AppExtensionType.__doc__)
AppExtensionViewEnum = to_enum(AppExtensionView, description=AppExtensionView.__doc__)
AppExtensionTargetEnum = to_enum(
    AppExtensionTarget, description=AppExtensionTarget.__doc__
)
