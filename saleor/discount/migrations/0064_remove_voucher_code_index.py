from django.db import migrations


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("discount", "0063_basediscount_voucher_code"),
    ]

    operations = [
        migrations.RunSQL(
            """
            DROP INDEX CONCURRENTLY IF EXISTS discount_voucher_code_ff8dc52c_like;
            """
        )
    ]
