-- Staging model: 1:1 cleaned/typed view over the raw_sales_transactions
-- seed. user_id is a foreign key to stg_names.user_id (enforced by the
-- `relationships` test in stg_sales_transactions.yml).
-- See models/docs.md for column-level documentation (doc blocks).
with source as (

    select * from {{ ref('raw_sales_transactions') }}

),

renamed as (

    select
        transaction_id,
        -- FK -> stg_names.user_id. Every row here represents one purchase
        -- made by that customer.
        user_id,
        -- FK -> stg_products.product_id. Join to stg_products for
        -- product_name/category rather than looking them up here, since
        -- this table only stores the point-in-time price/quantity.
        product_id,
        order_date,
        quantity,
        unit_price,
        -- unit_price * quantity, computed at generation time; not
        -- recalculated here so it reflects the originally recorded amount.
        total_amount,
        payment_method,
        region

    from source

)

select * from renamed
