# Generated by Django 3.0.6 on 2020-05-29 12:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0002_auto_20200520_0124"),
    ]

    operations = [
        migrations.RenameField(
            model_name="app",
            old_name="homepage_url",
            new_name="homepage_on_marketplace_url",
        ),
    ]
