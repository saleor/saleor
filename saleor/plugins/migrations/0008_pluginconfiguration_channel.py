import django.db.models.deletion
from django.db import migrations, models

PLUGINS_ID_TO_SKIP = [
    "mirumee.webhooks",
    "mirumee.payments.dummy",
    "mirumee.payments.dummy_credit_card",
    "mirumee.invoicing",
]


def move_company_address_to_avatax_configuration(apps, schema):
    avatax_configuration = (
        apps.get_model("plugins", "PluginConfiguration")
        .objects.filter(identifier="mirumee.taxes.avalara")
        .first()
    )
    if avatax_configuration and avatax_configuration.configuration:
        site_settings = apps.get_model("site", "SiteSettings").objects.first()
        configuration = avatax_configuration.configuration

        if company_address := site_settings.company_address:
            configuration.extend(
                [
                    {
                        "name": "from_street_address",
                        "value": company_address.street_address_1,
                    },
                    {
                        "name": "from_city",
                        "value": company_address.city,
                    },
                    {
                        "name": "from_country",
                        "value": company_address.country.code,
                    },
                    {
                        "name": "from_country_area",
                        "value": company_address.country_area,
                    },
                    {
                        "name": "from_postal_code",
                        "value": company_address.postal_code,
                    },
                ]
            )
            avatax_configuration.save()


def populate_plugin_configurations_for_channels(apps, schema):
    PluginConfiguration = apps.get_model("plugins", "PluginConfiguration")
    Channel = apps.get_model("channel", "Channel")

    channels = Channel.objects.all()
    configurations = PluginConfiguration.objects.exclude(
        identifier__in=PLUGINS_ID_TO_SKIP
    )

    for channel in channels:
        for configuration in configurations:
            configuration.id = None
            configuration.channel = channel
            configuration.save()

    configurations.filter(channel__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("channel", "0001_initial"),
        ("plugins", "0007_add_user_emails_configuration"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pluginconfiguration",
            name="identifier",
            field=models.CharField(max_length=128),
        ),
        migrations.AddField(
            model_name="pluginconfiguration",
            name="channel",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="channel.channel",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="pluginconfiguration",
            unique_together={("identifier", "channel")},
        ),
        migrations.RunPython(move_company_address_to_avatax_configuration),
        migrations.RunPython(populate_plugin_configurations_for_channels),
    ]
