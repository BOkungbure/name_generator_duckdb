-- Mart: product-grain aggregation on top of customer_sales. One row per
-- product_id, summarizing how much of it has sold and to how many distinct
-- customers. Powers "top products" / "best sellers" style reporting.
with customer_sales as (

    select * from {{ ref('customer_sales') }}

)

select
    product_id,
    product_name,
    category,
    count(transaction_id) as order_count,
    count(distinct user_id) as distinct_customers,
    sum(quantity) as total_units_sold,
    round(sum(total_amount), 2) as total_revenue,
    round(avg(unit_price), 2) as avg_unit_price

from customer_sales
group by 1, 2, 3
order by total_revenue desc
