from django.db import migrations, models


class Migration(migrations.Migration):
    atomic = True

    dependencies = [
        ("product", "0194_auto_20240620_1404"),
    ]

    operations = [
        migrations.AddField(
            model_name="categorytranslation",
            name="slug",
            field=models.SlugField(allow_unicode=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="collectiontranslation",
            name="slug",
            field=models.SlugField(allow_unicode=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="producttranslation",
            name="slug",
            field=models.SlugField(allow_unicode=True, max_length=255, null=True),
        ),
    ]
