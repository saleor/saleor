import graphene
import requests
from django.core.exceptions import ValidationError

from ....app.error_codes import AppErrorCode
from ....app.installation_utils import REQUEST_TIMEOUT
from ....app.manifest_validations import clean_manifest_data, clean_manifest_url
from ....core.permissions import AppPermission
from ...core import types as grapqhl_types
from ...core.enums import PermissionEnum
from ...core.mutations import BaseMutation
from ...core.types import AppError
from ..types import Manifest


class AppFetchManifest(BaseMutation):
    manifest = graphene.Field(Manifest)

    class Arguments:
        manifest_url = graphene.String(required=True)

    class Meta:
        description = "Fetch and validate manifest."
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = AppError
        error_type_field = "app_errors"

    @classmethod
    def success_response(cls, instance):
        """Return a success response."""
        return cls(manifest=instance, errors=[])

    @classmethod
    def fetch_manifest(cls, manifest_url):
        try:
            response = requests.get(manifest_url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.Timeout:
            msg = "The request to fetch manifest data timed out."
            code = AppErrorCode.MANIFEST_URL_CANT_CONNECT.value
            raise ValidationError({"manifest_url": ValidationError(msg, code=code)})
        except requests.HTTPError:
            msg = "Unable to fetch manifest data."
            code = AppErrorCode.MANIFEST_URL_CANT_CONNECT.value
            raise ValidationError({"manifest_url": ValidationError(msg, code=code)})
        except ValueError:
            msg = "Incorrect structure of manifest."
            code = AppErrorCode.INVALID_MANIFEST_FORMAT.value
            raise ValidationError({"manifest_url": ValidationError(msg, code=code)})
        except Exception:
            msg = "Can't fetch manifest data. Please try later."
            code = AppErrorCode.INVALID.value
            raise ValidationError({"manifest_url": ValidationError(msg, code=code)})

    @classmethod
    def construct_instance(cls, instance, cleaned_data):
        return Manifest(
            identifier=cleaned_data.get("id"),
            name=cleaned_data.get("name"),
            about=cleaned_data.get("about"),
            data_privacy=cleaned_data.get("dataPrivacy"),
            data_privacy_url=cleaned_data.get("dataPrivacyUrl"),
            homepage_url=cleaned_data.get("homepageUrl"),
            support_url=cleaned_data.get("supportUrl"),
            configuration_url=cleaned_data.get("configurationUrl"),
            app_url=cleaned_data.get("appUrl"),
            version=cleaned_data.get("version"),
            token_target_url=cleaned_data.get("tokenTargetUrl"),
            permissions=cleaned_data.get("permissions"),
            extensions=cleaned_data.get("extensions", []),
            webhooks=cleaned_data.get("webhooks", []),
            audience=cleaned_data.get("audience"),
        )

    @classmethod
    def clean_manifest_data(cls, info, manifest_data):
        clean_manifest_data(manifest_data)

        manifest_data["permissions"] = [
            grapqhl_types.Permission(
                code=PermissionEnum.get(p.formated_codename), name=p.name
            )
            for p in manifest_data["permissions"]
        ]
        for extension in manifest_data.get("extensions", []):
            extension["permissions"] = [
                grapqhl_types.Permission(
                    code=PermissionEnum.get(p.formated_codename),
                    name=p.name,
                )
                for p in extension["permissions"]
            ]

    @classmethod
    def perform_mutation(cls, _root, info, /, **data):
        manifest_url = data.get("manifest_url")
        clean_manifest_url(manifest_url)
        manifest_data = cls.fetch_manifest(manifest_url)
        cls.clean_manifest_data(info, manifest_data)

        instance = cls.construct_instance(instance=None, cleaned_data=manifest_data)
        return cls.success_response(instance)
