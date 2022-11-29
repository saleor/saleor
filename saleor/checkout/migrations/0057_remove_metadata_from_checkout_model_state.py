from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("checkout", "0056_move_checkout_metadata_to_separate_model"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            # Delete fields from state only, removal from db will happen in
            # next patch to prevent downtime and ensure backward-compatibility
            state_operations=[
                migrations.RemoveField(
                    model_name="checkout",
                    name="metadata",
                ),
                migrations.RemoveField(
                    model_name="checkout",
                    name="private_metadata",
                ),
                migrations.RemoveIndex(
                    model_name="checkout",
                    name="checkout_p_meta_idx",
                ),
                migrations.RemoveIndex(
                    model_name="checkout",
                    name="checkout_meta_idx",
                ),
            ],
        ),
    ]
