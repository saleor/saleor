from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0001_initial"),
        ("webhook", "0003_unmount_service_account"),
    ]
    state_operations = [
        migrations.AddField(
            model_name="webhook",
            name="app",
            field=models.ForeignKey(
                default="",
                on_delete=models.deletion.CASCADE,
                related_name="webhooks",
                to="app.App",
            ),
            preserve_default=False,
        ),
    ]
    operations = [
        migrations.SeparateDatabaseAndState(state_operations=state_operations)
    ]
