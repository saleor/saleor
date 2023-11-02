from django.db import migrations


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("discount", "0064_merge_20231020_1334"),
    ]

    operations = [
        migrations.RunSQL(
            """
            DROP INDEX CONCURRENTLY IF EXISTS discount_voucher_code_ff8dc52c_like;
            """,
            reverse_sql=migrations.RunSQL.noop,
        )
    ]
