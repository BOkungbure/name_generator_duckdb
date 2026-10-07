-- Mart: customer-grain aggregation on top of customer_sales. One row per
-- user_id, summarizing their full purchase history (lifetime value, order
-- count, first/last order dates). Powers "top customers" style reporting.
with customer_sales as (

    select * from {{ ref('customer_sales') }}

)

select
    user_id,
    full_name,
    email,
    state,
    country,
    count(transaction_id) as transaction_count,
    sum(quantity) as total_items_purchased,
    -- Core "how much has this customer spent" metric.
    round(sum(total_amount), 2) as lifetime_value,
    round(avg(total_amount), 2) as avg_order_value,
    min(order_date) as first_order_date,
    max(order_date) as last_order_date

from customer_sales
group by 1, 2, 3, 4, 5
order by lifetime_value desc
