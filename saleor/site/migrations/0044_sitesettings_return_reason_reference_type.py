import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("page", "0031_alter_page_metadata_alter_page_private_metadata_and_more"),
        ("site", "0043_sitesettings_use_legacy_update_webhook_emission"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sitesettings",
            name="refund_reason_reference_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="page.pagetype",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="return_reason_reference_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="page.pagetype",
            ),
        ),
    ]
