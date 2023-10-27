# Generated by Django 3.2.20 on 2023-08-16 12:09

import django.contrib.postgres.indexes
from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("channel", "0015_channel_use_legacy_error_flow_for_checkout"),
    ]

    operations = [
        AddIndexConcurrently(
            model_name="channel",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["private_metadata"], name="channel_p_meta_idx"
            ),
        ),
        AddIndexConcurrently(
            model_name="channel",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["metadata"], name="channel_meta_idx"
            ),
        ),
    ]
