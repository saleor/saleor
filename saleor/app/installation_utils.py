import requests
from django.contrib.sites.models import Site

from .manifest_validations import clean_manifest_data
from .models import App, AppInstallation
from .models import AppExtension
from .types import AppType
from ..core.permissions import get_permission_names

REQUEST_TIMEOUT = 25


def send_app_token(target_url: str, token: str):
    domain = Site.objects.get_current().domain
    headers = {"x-saleor-domain": domain, "Content-Type": "application/json"}
    json_data = {"auth_token": token}
    response = requests.post(
        target_url, json=json_data, headers=headers, timeout=REQUEST_TIMEOUT
    )
    response.raise_for_status()


def install_app(
    app_installation: AppInstallation,
    activate: bool = False,
):
    response = requests.get(app_installation.manifest_url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    assigned_permissions = app_installation.permissions.all()
    manifest_data = response.json()

    manifest_data["permissions"] = get_permission_names(assigned_permissions)

    clean_manifest_data(manifest_data)

    app = App.objects.create(
        name=app_installation.app_name,
        is_active=activate,
        identifier=manifest_data.get("id"),
        about_app=manifest_data.get("about"),
        data_privacy=manifest_data.get("dataPrivacy"),
        data_privacy_url=manifest_data.get("dataPrivacyUrl"),
        homepage_url=manifest_data.get("homepageUrl"),
        support_url=manifest_data.get("supportUrl"),
        configuration_url=manifest_data.get("configurationUrl"),
        app_url=manifest_data.get("appUrl"),
        version=manifest_data.get("version"),
        type=AppType.THIRDPARTY,
    )
    app.permissions.set(app_installation.permissions.all())
    for extension_data in manifest_data.get("extensions", []):
        extension = AppExtension.objects.create(
            app=app,
            label=extension_data.get("label"),
            url=extension_data.get("url"),
            view=extension_data.get("view"),
            type=extension_data.get("type"),
            target=extension_data.get("target"),
        )
        extension.permissions.set(extension_data.get("permissions", []))

    token = app.tokens.create(name="Default token")

    try:
        send_app_token(
            target_url=manifest_data.get("tokenTargetUrl"), token=token.auth_token
        )
    except requests.RequestException as e:
        app.delete()
        raise e
    return app
