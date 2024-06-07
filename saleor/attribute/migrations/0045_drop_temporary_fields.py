from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("attribute", "0044_reintroduce_attribute_value_constraints"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveField(
                    model_name="assignedpageattributevalue",
                    name="page_uniq",
                ),
                migrations.RemoveField(
                    model_name="assignedproductattributevalue",
                    name="product_uniq",
                ),
            ]
        )
    ]
