{% snapshot product_catalog_snapshot %}

{{
    config(
        unique_key="product_id",
        strategy="check",
        check_cols=["product_name", "category", "unit_price"]
    )
}}

select
    product_id,
    product_name,
    category,
    unit_price
from {{ ref("raw_products") }}

{% endsnapshot %}
