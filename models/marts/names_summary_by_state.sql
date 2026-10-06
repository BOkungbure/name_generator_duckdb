with names as (

    select * from {{ ref('stg_names') }}

)

select
    state,
    gender,
    count(*) as name_count,
    round(avg(age), 1) as avg_age

from names
group by 1, 2
order by 1, 2
