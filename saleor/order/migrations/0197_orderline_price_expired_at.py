# Generated by Django 4.2.16 on 2025-02-21 15:57

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("order", "0196_merge_20241014_0631"),
    ]

    operations = [
        migrations.AddField(
            model_name="orderline",
            name="price_expired_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
