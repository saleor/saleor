# Generated by Django 2.1.5 on 2019-03-01 09:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('site', '0019_sitesettings_default_weight_unit'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='sitesettings',
            options={'permissions': (('manage_settings', 'Manage settings.'), ('manage_translations', 'Manage translations.'))},
        ),
    ]
