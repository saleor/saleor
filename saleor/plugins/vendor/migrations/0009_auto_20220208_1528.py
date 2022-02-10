# Generated by Django 3.2.10 on 2022-02-08 15:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vendor", "0008_rename_vendors_billing_vendor"),
    ]

    operations = [
        migrations.RenameField(
            model_name="billing",
            old_name="iban_num",
            new_name="iban",
        ),
        migrations.AlterField(
            model_name="vendor",
            name="commercial_info",
            field=models.IntegerField(choices=[(1, "Cr"), (2, "Maroof")], default=1),
        ),
        migrations.AlterField(
            model_name="vendor",
            name="sells_gender",
            field=models.IntegerField(
                choices=[(1, "Men"), (2, "Women"), (3, "Unisex")], default=1
            ),
        ),
        migrations.AlterField(
            model_name="vendor",
            name="slug",
            field=models.SlugField(max_length=256, unique=True),
        ),
    ]
