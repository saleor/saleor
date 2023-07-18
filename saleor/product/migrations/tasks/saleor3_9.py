from ....celeryconf import app
from ...models import Product

from django.db.models import QuerySet, Q

from ....core.utils.editorjs import clean_editor_js


def set_description_plaintext(qs: QuerySet[Product]):
    for product in qs:
        product.description_plaintext = clean_editor_js(
            product.description, to_string=True
        )
        product.search_index_dirty = True

    Product.objects.bulk_update(qs, ["description_plaintext", "search_index_dirty"])


@app.task
def set_description_plaintext_task(last_pk: int = 0):
    filter_kwargs = {"pk__lt": last_pk} if last_pk else {}
    products = Product.objects.filter(
        Q(description_plaintext="", **filter_kwargs) & ~Q(description=None)
    ).order_by("-pk")

    ids = products.values_list("pk", flat=True)[:2000]
    qs = Product.objects.filter(pk__in=ids)

    if ids:
        set_description_plaintext(qs)
        set_description_plaintext_task.delay(tuple(ids)[0])
