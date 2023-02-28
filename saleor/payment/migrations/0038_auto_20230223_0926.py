from decimal import Decimal
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("account", "0075_add_address_metadata"),
        ("app", "0019_fix_constraint_names_in_app_app_permisons"),
        ("payment", "0037_alter_transaction_error"),
    ]

    operations = [
        migrations.AddField(
            model_name="transactionevent",
            name="amount_value",
            field=models.DecimalField(
                decimal_places=3, default=Decimal("0"), max_digits=12
            ),
        ),
        migrations.AddField(
            model_name="transactionevent",
            name="app",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="app.app",
            ),
        ),
        migrations.AddField(
            model_name="transactionevent",
            name="app_identifier",
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name="transactionevent",
            name="currency",
            field=models.CharField(blank=True, max_length=3, null=True),
        ),
        migrations.AddField(
            model_name="transactionevent",
            name="external_url",
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="transactionevent",
            name="include_in_calculations",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="transactionevent",
            name="message",
            field=models.CharField(blank=True, default="", max_length=512, null=True),
        ),
        migrations.AddField(
            model_name="transactionevent",
            name="psp_reference",
            field=models.CharField(blank=True, default="", max_length=512),
        ),
        migrations.AddField(
            model_name="transactionevent",
            name="type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("authorization_success", "Represents success authorization"),
                    ("authorization_failure", "Represents failure authorization"),
                    ("authorization_adjustment", "Represents authorization adjustment"),
                    ("authorization_request", "Represents authorization request"),
                    ("charge_success", "Represents success charge"),
                    ("charge_failure", "Represents failure charge"),
                    ("charge_back", "Represents chargeback."),
                    ("charge_request", "Represents charge request"),
                    ("refund_success", "Represents success refund"),
                    ("refund_failure", "Represents failure refund"),
                    ("refund_reverse", "Represents reverse refund"),
                    ("refund_request", "Represents refund request"),
                    ("cancel_success", "Represents success cancel"),
                    ("cancel_failure", "Represents failure cancel"),
                    ("cancel_request", "Represents cancel request"),
                ],
                max_length=128,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="transactionevent",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="account.user",
            ),
        ),
        migrations.AddField(
            model_name="transactionitem",
            name="app",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="app.app",
            ),
        ),
        migrations.AddField(
            model_name="transactionitem",
            name="app_identifier",
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name="transactionitem",
            name="authorize_pending_value",
            field=models.DecimalField(
                decimal_places=3, default=Decimal("0"), max_digits=12
            ),
        ),
        migrations.AddField(
            model_name="transactionitem",
            name="cancel_pending_value",
            field=models.DecimalField(
                decimal_places=3, default=Decimal("0"), max_digits=12
            ),
        ),
        migrations.AddField(
            model_name="transactionitem",
            name="canceled_value",
            field=models.DecimalField(
                decimal_places=3, default=Decimal("0"), max_digits=12
            ),
        ),
        migrations.AddField(
            model_name="transactionitem",
            name="charge_pending_value",
            field=models.DecimalField(
                decimal_places=3, default=Decimal("0"), max_digits=12
            ),
        ),
        migrations.AddField(
            model_name="transactionitem",
            name="external_url",
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="transactionitem",
            name="message",
            field=models.CharField(blank=True, default="", max_length=512, null=True),
        ),
        migrations.AddField(
            model_name="transactionitem",
            name="name",
            field=models.CharField(blank=True, default="", max_length=512, null=True),
        ),
        migrations.AddField(
            model_name="transactionitem",
            name="psp_reference",
            field=models.CharField(blank=True, max_length=512, null=True),
        ),
        migrations.AddField(
            model_name="transactionitem",
            name="refund_pending_value",
            field=models.DecimalField(
                decimal_places=3, default=Decimal("0"), max_digits=12
            ),
        ),
        migrations.AddField(
            model_name="transactionitem",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="account.user",
            ),
        ),
        migrations.AlterField(
            model_name="transactionevent",
            name="status",
            field=models.CharField(
                blank=True,
                choices=[
                    ("pending", "Pending"),
                    ("success", "Success"),
                    ("failure", "Failure"),
                ],
                default="success",
                max_length=128,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="transactionitem",
            name="status",
            field=models.CharField(blank=True, default="", max_length=512, null=True),
        ),
    ]
