from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("webhook", "0012_webhook_filterable_channel_slugs_idx"),
    ]

    operations = [
        migrations.AddField(
            model_name="webhook",
            name="identifier",
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddConstraint(
            model_name="webhook",
            constraint=models.CheckConstraint(
                condition=~models.Q(identifier=""),
                name="webhook_identifier_not_blank",
            ),
        ),
    ]
