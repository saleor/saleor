from django.db import migrations


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("account", "0105_add_manage_customer_types_and_attributes_perm"),
    ]

    operations = [
        migrations.RunSQL(
            sql="DROP INDEX CONCURRENTLY IF EXISTS idx_user_full_name;",
            reverse_sql=[
                "DROP INDEX CONCURRENTLY IF EXISTS idx_user_full_name;",
                """
                CREATE INDEX CONCURRENTLY idx_user_full_name
                ON account_user
                USING gin ((first_name || ' ' || last_name) gin_trgm_ops);
                """,
            ],
        ),
    ]
