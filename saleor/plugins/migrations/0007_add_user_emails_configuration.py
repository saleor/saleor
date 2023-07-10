import os

import dj_email_url
from django.conf import settings
from django.db import migrations
from django.utils.module_loading import import_string


def populate_email_config_in_user_email_plugin(apps, schema):
    user_email_path = "saleor.plugins.user_email.plugin.UserEmailPlugin"
    if user_email_path not in settings.PLUGINS:
        return

    # Allow to provide different email url from env
    email_url = os.environ.get("USER_EMAIL_URL", getattr(settings, "EMAIL_URL", None))

    if not email_url:
        return

    email_config = dj_email_url.parse(email_url)

    # Assume that EMAIL_URL has been split to partial env values
    email_config = {
        "host": email_config["EMAIL_HOST"],
        "port": email_config["EMAIL_PORT"],
        "username": email_config["EMAIL_HOST_USER"],
        "password": email_config["EMAIL_HOST_PASSWORD"],
        "sender_address": getattr(settings, "DEFAULT_FROM_EMAIL"),
        "use_tls": email_config["EMAIL_USE_TLS"],
        "use_ssl": email_config["EMAIL_USE_SSL"],
    }

    if not all(
        [email_config["host"], email_config["port"], email_config["sender_address"]]
    ):
        return

    UserEmail = import_string(user_email_path)
    configuration = UserEmail.DEFAULT_CONFIGURATION
    for configuration_field in configuration:
        config_name = configuration_field["name"]
        if config_name in email_config:
            configuration_field["value"] = email_config[config_name]

    PluginConfiguration = apps.get_model("plugins", "PluginConfiguration")
    plugin_configuration, _ = PluginConfiguration.objects.get_or_create(
        identifier=UserEmail.PLUGIN_ID,
        defaults={"active": True, "configuration": configuration},
    )


class Migration(migrations.Migration):
    dependencies = [
        ("plugins", "0006_auto_20200909_1253"),
    ]

    operations = [
        migrations.RunPython(populate_email_config_in_user_email_plugin),
    ]
