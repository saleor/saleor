import graphene

from ....csv import models as csv_models
from ....csv.events import export_started_event
from ....csv.tasks import export_gift_cards_task
from ....permission.enums import GiftcardPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_31
from ...core.doc_category import DOC_CATEGORY_GIFT_CARDS
from ...core.types import BaseInputObjectType, ExportError, NonNullList
from ...core.utils import WebhookEventInfo
from ...giftcard.filters import GiftCardFilterInput
from ...giftcard.types import GiftCard
from ..enums import ExportScope, FileTypeEnum
from .base_export import BaseExportMutation


class ExportGiftCardsInput(BaseInputObjectType):
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

    class Meta:
        doc_category = DOC_CATEGORY_GIFT_CARDS


class ExportGiftCards(BaseExportMutation):
    class Arguments:
        input = ExportGiftCardsInput(
            required=True, description="Fields required to export gift cards data."
        )

    class Meta:
        description = "Export gift cards to csv file." + ADDED_IN_31
        doc_category = DOC_CATEGORY_GIFT_CARDS
        permissions = (GiftcardPermissions.MANAGE_GIFT_CARD,)
        error_type_class = ExportError
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.NOTIFY_USER,
                description="A notification for the exported file.",
            ),
        ]

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, input
    ):
        scope = cls.get_scope(input, GiftCard)
        file_type = input["file_type"]

        app = get_app_promise(info.context).get()

        export_file = csv_models.ExportFile.objects.create(
            app=app, user=info.context.user
        )
        export_started_event(export_file=export_file, app=app, user=info.context.user)
        export_gift_cards_task.delay(export_file.pk, scope, file_type)

        export_file.refresh_from_db()
        return cls(export_file=export_file)
