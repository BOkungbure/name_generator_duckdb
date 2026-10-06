with source as (

    select * from {{ ref('raw_names') }}

),

renamed as (

    select
        id as name_id,
        user_id,
        first_name,
        last_name,
        full_name,
        gender,
        lower(email) as email,
        phone_number,
        birthdate,
        city,
        state,
        country,
        created_at,
        date_diff('year', birthdate, current_date) as age

    from source

)

select * from renamed
