import django.db.models.deletion
from django.db import migrations, models

PLUGINS_ID_TO_SKIP = [
    "mirumee.webhooks",
    "mirumee.payments.dummy",
    "mirumee.payments.dummy_credit_card",
    "mirumee.invoicing",
]


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
        migrations.RunPython(populate_plugin_configurations_for_channels),
    ]
