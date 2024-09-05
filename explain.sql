-- -- Usage:
-- -- psql -XqAt postgresql://saleor:saleor@localhost:5432/saleor -f explain.sql > analyze.json
EXPLAIN (ANALYZE, COSTS, VERBOSE, BUFFERS, FORMAT JSON)
SELECT
    "product_productvariant"."id",
    "product_productvariant"."sort_order",
    "product_productvariant"."private_metadata",
    "product_productvariant"."metadata",
    "product_productvariant"."external_reference",
    "product_productvariant"."sku",
    "product_productvariant"."name",
    "product_productvariant"."product_id",
    "product_productvariant"."track_inventory",
    "product_productvariant"."is_preorder",
    "product_productvariant"."preorder_end_date",
    "product_productvariant"."preorder_global_threshold",
    "product_productvariant"."quantity_limit_per_customer",
    "product_productvariant"."created_at",
    "product_productvariant"."updated_at",
    "product_productvariant"."weight"
FROM
    "product_productvariant"
WHERE
    (
        EXISTS(
            SELECT
                (1) AS "a"
            FROM
                "product_productvariantchannellisting" U0
            WHERE
                (
                    U0."channel_id" = 2
                    AND U0."price_amount" IS NOT NULL
                    AND U0."variant_id" = "product_productvariant"."id"
                )
            LIMIT
                1
        )
        AND "product_productvariant"."product_id" IN (83992)
    )
ORDER BY
    "product_productvariant"."sort_order" ASC,
    "product_productvariant"."sku" ASC
