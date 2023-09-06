from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("page", "0028_add_default_page_type"),
        ("attribute", "0031_extend_attributr_value_fields_length"),
    ]

    operations = [
        migrations.AddField(
            model_name="assignedpageattributevalue",
            name="page",
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="attributevalues",
                to="page.page",
                db_index=False,
            ),
        ),
    ]
