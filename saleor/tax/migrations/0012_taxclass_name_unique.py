# Generated manually for https://github.com/saleor/saleor/issues/15181

from django.db import migrations, models
from django.db.models import Count


def make_tax_class_names_unique(apps, schema_editor):
    TaxClass = apps.get_model("tax", "TaxClass")
    duplicate_names = list(
        TaxClass.objects.values("name")
        .annotate(name_count=Count("id"))
        .filter(name_count__gt=1)
        .values_list("name", flat=True)
    )
    for name in duplicate_names:
        duplicates = list(TaxClass.objects.filter(name=name).order_by("pk"))
        for tax_class in duplicates[1:]:
            new_name = f"{name} ({tax_class.pk})"
            while TaxClass.objects.filter(name=new_name).exists():
                new_name = f"{new_name}*"
            tax_class.name = new_name
            tax_class.save(update_fields=["name"])


class Migration(migrations.Migration):
    dependencies = [
        ("tax", "0011_merge_20250530_0929"),
    ]

    operations = [
        migrations.RunPython(
            make_tax_class_names_unique,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="taxclass",
            name="name",
            field=models.CharField(max_length=255, unique=True),
        ),
    ]
