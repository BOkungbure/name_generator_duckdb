-- Staging model: 1:1 cleaned/typed view over the raw.names source table.
-- See models/docs.md for column-level documentation (doc blocks).
with source as (

    select * from {{ source('raw', 'names') }}

),

renamed as (

    select
        -- Rename the database-generated surrogate key; use user_id for joins.
        id as name_id,
        user_id,
        first_name,
        last_name,
        full_name,
        gender,
        -- Normalize email casing so joins/uniqueness tests aren't tripped
        -- up by case differences.
        lower(email) as email,
        phone_number,
        birthdate,
        city,
        state,
        country,
        created_at,
        -- Derived column: current age in full years. Recomputed on every
        -- run, so this value can change over time even if the source data
        -- doesn't.
        extract(year from age(current_date, birthdate))::integer as age

    from source

)

select * from renamed
