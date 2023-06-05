import graphene
import requests
from django.core.exceptions import ValidationError

from ....app.error_codes import AppErrorCode
from ....app.installation_utils import fetch_manifest
from ....app.manifest_schema import Manifest as ManifestSchema
from ....app.manifest_validations import clean_manifest_url
from ....permission.enums import AppPermission
from ...core.doc_category import DOC_CATEGORY_APPS
from ...core.mutations import BaseMutation
from ...core.types import AppError
from ..types import Manifest

FETCH_BRAND_DATA_TIMEOUT = 5


class AppFetchManifest(BaseMutation):
    manifest = graphene.Field(Manifest, description="The validated manifest.")

    class Arguments:
        manifest_url = graphene.String(
            required=True, description="URL to app's manifest in JSON format."
        )

    class Meta:
        description = "Fetch and validate manifest."
        doc_category = DOC_CATEGORY_APPS
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = AppError
        error_type_field = "app_errors"

    @classmethod
    def success_response(cls, instance):
        """Return a success response."""
        return cls(manifest=instance, errors=[])

    @classmethod
    def fetch_manifest(cls, manifest_url) -> ManifestSchema:
        try:
            manifest_data = fetch_manifest(manifest_url)
            manifest = ManifestSchema.parse_obj(
                manifest_data, root_error_field="manifest_url"
            )
            return manifest
        except ValidationError as error:
            raise error
        except requests.Timeout:
            msg = "The request to fetch manifest data timed out."
            code = AppErrorCode.MANIFEST_URL_CANT_CONNECT.value
            raise ValidationError({"manifest_url": ValidationError(msg, code=code)})
        except requests.HTTPError:
            msg = "Unable to fetch manifest data."
            code = AppErrorCode.MANIFEST_URL_CANT_CONNECT.value
            raise ValidationError({"manifest_url": ValidationError(msg, code=code)})
        except Exception:
            msg = "Can't fetch manifest data. Please try later."
            code = AppErrorCode.INVALID.value
            raise ValidationError({"manifest_url": ValidationError(msg, code=code)})

    @classmethod
    def construct_instance(cls, instance, cleaned_data: ManifestSchema):
        return Manifest(
            identifier=cleaned_data.id,
            name=cleaned_data.name,
            about=cleaned_data.about,
            data_privacy=cleaned_data.data_privacy,
            data_privacy_url=cleaned_data.data_privacy_url,
            homepage_url=cleaned_data.homepage_url,
            support_url=cleaned_data.support_url,
            configuration_url=cleaned_data.configuration_url,
            app_url=cleaned_data.app_url,
            version=cleaned_data.version,
            token_target_url=cleaned_data.token_target_url,
            permissions=cleaned_data.permissions,
            extensions=cleaned_data.extensions,
            webhooks=cleaned_data.webhooks,
            audience=cleaned_data.audience,
            required_saleor_version=cleaned_data.required_saleor_version,
            author=cleaned_data.author,
        )

    @classmethod
    def perform_mutation(cls, _root, info, /, **data):
        manifest_url = data.get("manifest_url")
        clean_manifest_url(manifest_url)
        manifest_data = cls.fetch_manifest(manifest_url)

        instance = cls.construct_instance(instance=None, cleaned_data=manifest_data)
        return cls.success_response(instance)
