import graphene

from ....core.permissions import GiftcardPermissions
from ....csv import models as csv_models
from ....csv.events import export_started_event
from ....csv.tasks import export_gift_cards_task
from ...app.dataloaders import load_app
from ...core.descriptions import ADDED_IN_31, PREVIEW_FEATURE
from ...core.types import ExportError, NonNullList
from ...giftcard.filters import GiftCardFilterInput
from ...giftcard.types import GiftCard
from ..enums import ExportScope, FileTypeEnum
from .base_export import BaseExportMutation


class ExportGiftCardsInput(graphene.InputObjectType):
    scope = ExportScope(
        description="Determine which gift cards should be exported.", required=True
    )
    filter = GiftCardFilterInput(
        description="Filtering options for gift cards.", required=False
    )
    ids = NonNullList(
        graphene.ID,
        description="List of gift cards IDs to export.",
        required=False,
    )
    file_type = FileTypeEnum(description="Type of exported file.", required=True)


class ExportGiftCards(BaseExportMutation):
    class Arguments:
        input = ExportGiftCardsInput(
            required=True, description="Fields required to export gift cards data."
        )

    class Meta:
        description = "Export gift cards to csv file." + ADDED_IN_31 + PREVIEW_FEATURE
        permissions = (GiftcardPermissions.MANAGE_GIFT_CARD,)
        error_type_class = ExportError

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        input = data["input"]
        scope = cls.get_scope(input, GiftCard)
        file_type = input["file_type"]

        app = load_app(info.context)
        kwargs = {"app": app} if app else {"user": info.context.user}

        export_file = csv_models.ExportFile.objects.create(**kwargs)
        export_started_event(export_file=export_file, **kwargs)
        export_gift_cards_task.delay(export_file.pk, scope, file_type)

        export_file.refresh_from_db()
        return cls(export_file=export_file)
