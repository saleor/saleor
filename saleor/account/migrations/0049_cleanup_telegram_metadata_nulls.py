# Generated manually to cleanup Telegram metadata null values

from django.db import migrations


def cleanup_telegram_metadata_nulls(apps, schema_editor):
    """Clean up null values in Telegram user metadata"""
    User = apps.get_model("account", "User")

    # Find users with Telegram metadata
    telegram_users = User.objects.filter(external_reference__startswith="telegram_")

    cleaned_count = 0
    for user in telegram_users:
        if not user.private_metadata:
            continue

        original_metadata = user.private_metadata.copy()
        cleaned_metadata = {}

        # Clean up null values
        for key, value in original_metadata.items():
            if value is not None:
                cleaned_metadata[key] = value
            # Skip null values - they will be converted to empty strings by the resolver

        # Only update if there were changes
        if cleaned_metadata != original_metadata:
            user.private_metadata = cleaned_metadata
            user.save(update_fields=["private_metadata"])
            cleaned_count += 1

    print(f"Cleaned up metadata for {cleaned_count} Telegram users")


def reverse_cleanup_telegram_metadata_nulls(apps, schema_editor):
    """Reverse migration - this is a data cleanup, so reverse is no-op"""
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("account", "0048_auto_20210308_1135"),
    ]

    operations = [
        migrations.RunPython(
            cleanup_telegram_metadata_nulls,
            reverse_cleanup_telegram_metadata_nulls,
        ),
    ]
