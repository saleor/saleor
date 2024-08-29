from django.db import migrations, models


class Migration(migrations.Migration):
    atomic = True

    dependencies = [
        ("page", "0028_add_default_page_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="pagetranslation",
            name="slug",
            field=models.SlugField(allow_unicode=True, max_length=255, null=True),
        ),
    ]
