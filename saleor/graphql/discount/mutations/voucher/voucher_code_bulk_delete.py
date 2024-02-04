import graphene

from .....core.tracing import traced_atomic_transaction
from .....discount import models
from .....permission.enums import DiscountPermissions
from .....webhook.event_types import WebhookEventAsyncType
from ....core.descriptions import ADDED_IN_318
from ....core.doc_category import DOC_CATEGORY_DISCOUNTS
from ....core.enums import VoucherCodeBulkDeleteErrorCode
from ....core.mutations import BaseMutation
from ....core.types import NonNullList, VoucherCodeBulkDeleteError
from ....core.utils import WebhookEventInfo
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import VoucherCode


class VoucherCodeBulkDelete(BaseMutation):
    count = graphene.Int(
        required=True, description="Returns how many codes were deleted."
    )

    class Arguments:
        ids = NonNullList(
            graphene.ID,
            required=True,
            description="List of voucher codes IDs to delete.",
        )

    class Meta:
        description = "Deletes voucher codes." + ADDED_IN_318
        model = models.VoucherCode
        object_type = VoucherCode
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = VoucherCodeBulkDeleteError
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.VOUCHER_CODES_DELETED,
                description="A voucher codes were deleted.",
            ),
        ]
        doc_category = DOC_CATEGORY_DISCOUNTS

    @classmethod
    def clean_codes(cls, codes, errors_list):
        invalid_codes_ids = []
        cleaned_ids = set()

        for index, code in enumerate(codes):
            obj_type, code_pk = graphene.Node.from_global_id(code)
            if obj_type != "VoucherCode":
                invalid_codes_ids.append(code)
                continue

            cleaned_ids.add(code_pk)

        if invalid_codes_ids:
            errors_list.append(
                VoucherCodeBulkDeleteError(
                    path="ids",
                    code=VoucherCodeBulkDeleteErrorCode.INVALID.value,
                    message="Invalid VoucherCode ID.",
                    voucher_codes=invalid_codes_ids,
                )
            )
        return cleaned_ids

    @classmethod
    def post_save_actions(cls, info, codes_instances):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(
            manager.voucher_codes_deleted,
            codes_instances,
        )

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, root, info, **data):
        errors_list: list[VoucherCodeBulkDeleteError] = []
        cleaned_ids = cls.clean_codes(data["ids"], errors_list)

        if errors_list:
            return VoucherCodeBulkDelete(count=0, errors=errors_list)

        code_instances = models.VoucherCode.objects.filter(
            id__in=cleaned_ids
        ).select_related("voucher")

        count = len(code_instances)

        # Copy deleted instance and reassign the original IDs
        ids_and_codes_tuple = [(code.id, code) for code in code_instances]
        code_instances.delete()

        for id, code in ids_and_codes_tuple:
            code.id = id

        cls.post_save_actions(
            info, [id_and_code[1] for id_and_code in ids_and_codes_tuple]
        )

        return VoucherCodeBulkDelete(count=count)
