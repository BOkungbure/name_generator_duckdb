with customers as (

    select * from {{ ref('stg_names') }}

),

sales as (

    select * from {{ ref('stg_sales_transactions') }}

)

select
    customers.user_id,
    customers.full_name,
    customers.email,
    customers.state,
    customers.country,
    sales.transaction_id,
    sales.order_date,
    sales.product_name,
    sales.category,
    sales.quantity,
    sales.unit_price,
    sales.total_amount,
    sales.payment_method,
    sales.region

from customers
inner join sales
    on customers.user_id = sales.user_id
