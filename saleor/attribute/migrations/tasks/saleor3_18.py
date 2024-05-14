from ....celeryconf import app
from ...models import AssignedPageAttributeValue, AssignedProductAttributeValue

# TODO: change to ORM


@app.task()
def copy_product_id():
    AssignedProductAttributeValue.objects.raw(
        """
        SELECT MIN(id) AS id, product_id FROM ATTRIBUTE_ASSIGNEDPRODUCTATTRIBUTEVALUE
        GROUP BY PRODUCT_ID, VALUE_ID
        HAVING AVG(PRODUCT_UNIQ) IS NULL;
        """
    )


@app.task()
def copy_page_id():
    AssignedPageAttributeValue.objects.raw(
        """
        UPDATE ATTRIBUTE_ASSIGNEDPAGEATTRIBUTEVALUE aa
        SET PAGE_UNIQ = t.PAGE_ID
        FROM (
            SELECT MIN(id) AS id, page_id, VALUE_ID
            FROM ATTRIBUTE_ASSIGNEDPAGEATTRIBUTEVALUE
            GROUP BY PAGE_ID, VALUE_ID
            HAVING AVG(PAGE_UNIQ) IS NULL
            LIMIT 100
        ) t
        WHERE aa.id = t.id;
        """
    )
