with source as (

    select * from {{ ref('raw_sales_transactions') }}

),

renamed as (

    select
        transaction_id,
        user_id,
        order_date,
        product_name,
        category,
        quantity,
        unit_price,
        total_amount,
        payment_method,
        region

    from source

)

select * from renamed
