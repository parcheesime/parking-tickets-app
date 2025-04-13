-- Cleaned and renamed fields from the raw parking tickets data

select
  rp_state_plate as plate_state,
  agency,
  agency_desc,
  body_style,
  body_style_desc,
  color,
  color_desc,
  fine_amount,
  issue_date,
  issue_time,
  loc_lat,
  loc_long,
  location,
  make,
  marked_time,
  meter_id,
  plate_expiry_date,
  plate_state,
  ticket_number,
  violation_code,
  violation_description
from {{ ref('parking_tickets') }}
