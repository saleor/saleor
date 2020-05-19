import requests
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import transaction

from .models import App, AppInstallation
from .types import AppType

REQUEST_TIMEOUT = 30


def send_app_token(target_url: str, token: str):
    domain = Site.objects.get_current().domain
    headers = {"x-saleor-domain": domain, "Content-Type": "application/json"}
    json_data = {"auth_token": token}
    response = requests.post(
        target_url, json=json_data, headers=headers, timeout=REQUEST_TIMEOUT
    )
    response.raise_for_status()


def validate_manifest_fields(manifest_data):
    token_target_url = manifest_data.get("token_target_url")

    try:
        url_validator = URLValidator()
        url_validator(token_target_url)
    except ValidationError:
        raise ValidationError({"token_target_url": "Incorrect format."})


@transaction.atomic
def install_app(
    app_installation: AppInstallation, activate: bool = False,
):
    response = requests.get(app_installation.manifest_url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    manifest_data = response.json()

    validate_manifest_fields(manifest_data)

    app = App.objects.create(
        name=app_installation.app_name,
        is_active=activate,
        identificator=manifest_data.get("identificator"),
        about_app=manifest_data.get("about_app"),
        data_privacy=manifest_data.get("data_privacy"),
        data_privacy_url=manifest_data.get("data_privacy_url"),
        homepage_url=manifest_data.get("homepage_url"),
        support_url=manifest_data.get("support_url"),
        configuration_url=manifest_data.get("configuration_url"),
        app_url=manifest_data.get("app_url"),
        version=manifest_data.get("version"),
        type=AppType.EXTERNAL,
    )
    app.permissions.set(app_installation.permissions.all())
    token = app.tokens.create(name="Default token")
    send_app_token(
        target_url=manifest_data.get("token_target_url"), token=token.auth_token
    )
    return app
