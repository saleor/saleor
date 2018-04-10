# Generated by Django 2.0.3 on 2018-04-03 18:37

import logging
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import versatileimagefield.fields
from ...core.utils.random_data import create_homepage_blocks_by_schema
from ...core.management.commands import populatedb

logger = logging.getLogger(__name__)


def generate_default_homepage_blocks(*_):
    for msg in create_homepage_blocks_by_schema(
            populatedb.Command.placeholders_dir):
        logger.info(msg)


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('page', '0002_auto_20180321_0417'),
        ('product', '0056_auto_20180330_0321'),
    ]

    operations = [
        migrations.CreateModel(
            name='HomePageItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100, validators=[django.core.validators.MaxLengthValidator(100)])),
                ('subtitle', models.CharField(blank=True, max_length=255, null=True, validators=[django.core.validators.MaxLengthValidator(255)])),
                ('html_classes', models.CharField(blank=True, default='col-sm-12 col-md-6', max_length=100, validators=[django.core.validators.MaxLengthValidator(100)])),
                ('primary_button_text', models.CharField(blank=True, max_length=100, null=True, validators=[django.core.validators.MaxLengthValidator(100)])),
                ('cover', versatileimagefield.fields.VersatileImageField(blank=True, upload_to='homepage_blocks')),
                ('position', models.fields.PositiveIntegerField(
                    editable=False)),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='product.Category')),
                ('collection', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='product.Collection')),
                ('page', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='page.Page')),
            ],
            options={
                'ordering': ('position',),
                'permissions': (
                    ('view_blocks_config', 'Can view home page configuration'),
                    ('edit_blocks_config', 'Can edit home page configuration')
                ),
            },
        ),
        migrations.RunPython(generate_default_homepage_blocks)
    ]
