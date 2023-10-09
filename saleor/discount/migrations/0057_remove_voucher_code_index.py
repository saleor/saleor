from django.db import migrations


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("discount", "0056_set_vouchercustomer_codes"),
    ]

    operations = [
        migrations.RunSQL(
            """
            DROP INDEX CONCURRENTLY IF EXISTS discount_voucher_code_ff8dc52c_like;
            """
        )
    ]
