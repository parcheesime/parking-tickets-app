-- Cleaned, calculated metrics from staging model

select
  ticket_number,
  violation_code,
  violation_description,
  plate_state,
  fine_amount,
  issue_date,
  make,
  location,
  color,
  body_style,
  fine_amount / nullif(length(violation_description), 0) as cost_per_char_violation
from {{ ref('stg_parking_tickets') }}
where fine_amount is not null
