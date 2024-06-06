from django.db import connection

from ....celeryconf import app

BATCH = 1000


@app.task()
def copy_product_id():
    with connection.cursor() as cursor:
        # The query will group by pair of values with the idea of getting duplicates
        # in that pair and then copy the id to the temporary field, tricks used:
        # min(id) - we need one pair of values with the id, we take the oldest one, but
        # max would have also worked
        # AVG(PRODUCT_UNIQ) - if value is not null it means we already have one value
        # in the database with copied id to temporary field
        cursor.execute(
            """
            UPDATE ATTRIBUTE_ASSIGNEDPRODUCTATTRIBUTEVALUE aa
            SET PRODUCT_UNIQ = t.PRODUCT_ID
            FROM (
                SELECT MIN(id) AS id, product_id
                FROM ATTRIBUTE_ASSIGNEDPRODUCTATTRIBUTEVALUE
                GROUP BY PRODUCT_ID, VALUE_ID
                HAVING AVG(PRODUCT_UNIQ) IS NULL
                LIMIT %s
            ) t
            WHERE aa.id = t.id;
            """,
            [BATCH],
        )

        cursor.execute(
            """
            SELECT EXISTS(
                SELECT 1
                FROM ATTRIBUTE_ASSIGNEDPRODUCTATTRIBUTEVALUE
                GROUP BY PRODUCT_ID, VALUE_ID
                HAVING AVG(PRODUCT_UNIQ) IS NULL
            );
            """
        )
        result = cursor.fetchone()

    if result and result[0]:
        copy_product_id.delay()
    else:
        remove_product_id_duplicates.delay()


@app.task()
def remove_product_id_duplicates():
    with connection.cursor() as cursor:
        # We can remove duplicates. Using raw delete for better performance.
        cursor.execute(
            """
            DELETE FROM ATTRIBUTE_ASSIGNEDPRODUCTATTRIBUTEVALUE aa
            WHERE aa.id IN (
	            SELECT tt.id FROM ATTRIBUTE_ASSIGNEDPRODUCTATTRIBUTEVALUE tt
	            WHERE tt.product_uniq IS NULL
	            ORDER BY tt.id
	            LIMIT %s
            );
            """,
            [BATCH],
        )

        cursor.execute(
            """
            SELECT EXISTS(
                SELECT 1 FROM ATTRIBUTE_ASSIGNEDPRODUCTATTRIBUTEVALUE
                WHERE product_uniq IS NULL
            );
            """
        )

        result = cursor.fetchone()

    if result and result[0]:
        remove_product_id_duplicates.delay()


@app.task()
def copy_page_id():
    with connection.cursor() as cursor:
        # The query will group by pair of values with the idea of getting duplicates
        # in that pair and then copy the id to the temporary field, tricks used:
        # min(id) - we need one pair of values with the id, we take the oldest one, but
        # max would have also worked
        # AVG(PAGE_UNIQ) - if value is not null it means we already have one value
        # in the database with copied id to temporary field
        cursor.execute(
            """
            UPDATE ATTRIBUTE_ASSIGNEDPAGEATTRIBUTEVALUE aa
            SET PAGE_UNIQ = t.PAGE_ID
            FROM (
                SELECT MIN(id) AS id, page_id
                FROM ATTRIBUTE_ASSIGNEDPAGEATTRIBUTEVALUE
                GROUP BY PAGE_ID, VALUE_ID
                HAVING AVG(PAGE_UNIQ) IS NULL
                LIMIT %s
            ) t
            WHERE aa.id = t.id;
            """,
            [BATCH],
        )

        cursor.execute(
            """
            SELECT EXISTS(
                SELECT 1
                FROM ATTRIBUTE_ASSIGNEDPAGEATTRIBUTEVALUE
                GROUP BY PAGE_ID, VALUE_ID
                HAVING AVG(PAGE_UNIQ) IS NULL
            );
            """
        )
        result = cursor.fetchone()

    if result and result[0]:
        copy_page_id.delay()
    else:
        remove_page_id_duplicates.delay()


@app.task()
def remove_page_id_duplicates():
    with connection.cursor() as cursor:
        # We can remove duplicates. Using raw delete for better performance.
        cursor.execute(
            """
            DELETE FROM ATTRIBUTE_ASSIGNEDPAGEATTRIBUTEVALUE aa
            WHERE aa.id IN (
	            SELECT tt.id FROM ATTRIBUTE_ASSIGNEDPAGEATTRIBUTEVALUE tt
	            WHERE tt.page_uniq IS NULL
	            ORDER BY tt.id
	            LIMIT %s
            );
            """,
            [BATCH],
        )

        cursor.execute(
            """
            SELECT EXISTS(
                SELECT 1 FROM ATTRIBUTE_ASSIGNEDPAGEATTRIBUTEVALUE
                WHERE page_uniq IS NULL
            );
            """
        )

        result = cursor.fetchone()

    if result and result[0]:
        remove_page_id_duplicates.delay()
