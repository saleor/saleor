# Migration #13884: Migration changed to a no-op. The original
# fill_empty_passwords logic has been moved to a Celery task
# for performance reasons on large databases.


from django.db import migrations

def noop(apps, schema_editor):
    # The original logic for filling empty passwords has been moved to a Celery task.
    # Please run the corresponding Celery task after migrating.
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('account', '0075_auto_something'),  # Replace with actual upstream migration
    ]

    operations = [
        migrations.RunPython(noop, noop),
    ]
