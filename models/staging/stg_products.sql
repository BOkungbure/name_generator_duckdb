-- Staging model: 1:1 cleaned/typed view over the raw_products seed.
-- This is the "product dimension" that stg_sales_transactions joins
-- against via product_id.
-- See models/docs.md for column-level documentation (doc blocks).
with source as (

    select * from {{ ref('raw_products') }}

),

renamed as (

    select
        product_id,
        product_name,
        category,
        unit_price

    from source

)

select * from renamed
