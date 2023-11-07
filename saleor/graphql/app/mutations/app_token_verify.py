import graphene
from django.contrib.auth.hashers import check_password
from django.db.models import Exists, OuterRef, Q

from ....app import models
from ...core.doc_category import DOC_CATEGORY_APPS
from ...core.mutations import BaseMutation
from ...core.types import AppError


class AppTokenVerify(BaseMutation):
    valid = graphene.Boolean(
        default_value=False,
        required=True,
        description="Determine if token is valid or not.",
    )

    class Arguments:
        token = graphene.String(description="App token to verify.", required=True)

    class Meta:
        description = "Verify provided app token."
        doc_category = DOC_CATEGORY_APPS
        error_type_class = AppError
        error_type_field = "app_errors"

    @classmethod
    def perform_mutation(cls, _root, _info, /, *, token: str):  # type: ignore[override]
        apps = models.App.objects.filter(
            is_active=True, removed_at__isnull=True
        ).values("pk")
        tokens = models.AppToken.objects.filter(
            Q(token_last_4=token[-4:]), Exists(apps.filter(pk=OuterRef("app_id")))
        ).values_list("auth_token", flat=True)
        valid = any([check_password(token, auth_token) for auth_token in tokens])
        return AppTokenVerify(valid=valid)
