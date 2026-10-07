-- Staging model: 1:1 cleaned/typed view over the raw_names seed.
-- See models/docs.md for column-level documentation (doc blocks).
with source as (

    select * from {{ ref('raw_names') }}

),

renamed as (

    select
        -- Rename the seed's sequential id to make its role explicit; it is
        -- NOT a stable join key (use user_id for that).
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
        -- run, so this value can change over time even if the underlying
        -- seed data doesn't.
        date_diff('year', birthdate, current_date) as age

    from source

)

select * from renamed
