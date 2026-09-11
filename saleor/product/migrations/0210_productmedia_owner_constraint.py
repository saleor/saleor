from django.db import migrations, models

from ..models import at_most_one_media_owner_condition

CONSTRAINT_NAME = "productmedia_at_most_one_owner"


class Migration(migrations.Migration):
    # ADD CONSTRAINT ... NOT VALID and VALIDATE CONSTRAINT must be separate
    # transactions, otherwise the validating scan holds the ACCESS EXCLUSIVE lock
    # taken by the ALTER TABLE.
    atomic = False

    dependencies = [
        ("product", "0209_productmedia_owner_indexes"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=f"""
                    ALTER TABLE product_productmedia
                    ADD CONSTRAINT {CONSTRAINT_NAME}
                    CHECK (
                        num_nonnulls(product_id, category_id, collection_id, page_id)
                        <= 1
                    ) NOT VALID;
                    """,
                    reverse_sql=f"""
                    ALTER TABLE product_productmedia
                    DROP CONSTRAINT IF EXISTS {CONSTRAINT_NAME};
                    """,
                ),
                migrations.RunSQL(
                    sql=f"""
                    ALTER TABLE product_productmedia
                    VALIDATE CONSTRAINT {CONSTRAINT_NAME};
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.AddConstraint(
                    model_name="productmedia",
                    constraint=models.CheckConstraint(
                        condition=at_most_one_media_owner_condition(),
                        name=CONSTRAINT_NAME,
                    ),
                ),
            ],
        ),
    ]
