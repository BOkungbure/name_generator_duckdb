-- Mart: row-level join between customers (stg_names), their sales
-- transactions (stg_sales_transactions), and the product purchased
-- (stg_products) on user_id / product_id.
--
-- NOTE: the customer join is an INNER JOIN, so customers with zero
-- transactions are intentionally excluded here. For a full customer list
-- including non-purchasers, join stg_names to customer_sales_summary with
-- a LEFT JOIN instead.
with customers as (

    select * from {{ ref('stg_names') }}

),

sales as (

    select * from {{ ref('stg_sales_transactions') }}

),

products as (

    select * from {{ ref('stg_products') }}

)

select
    customers.user_id,
    customers.full_name,
    customers.email,
    customers.state,
    customers.country,
    sales.transaction_id,
    sales.order_date,
    products.product_id,
    products.product_name,
    products.category,
    sales.quantity,
    sales.unit_price,
    sales.total_amount,
    sales.payment_method,
    sales.region

from customers
inner join sales
    on customers.user_id = sales.user_id
inner join products
    on sales.product_id = products.product_id
