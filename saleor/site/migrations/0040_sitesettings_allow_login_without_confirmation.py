from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("site", "0039_auto_20230615_1754"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="allow_login_without_confirmation",
            field=models.BooleanField(default=False),
        ),
        migrations.RunSQL(
            sql="""
            ALTER TABLE site_sitesettings
            ALTER COLUMN allow_login_without_confirmation
            SET DEFAULT false;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
