# Parking Ticket Data Exploration

## Description of Data

| Column Name            | Description             | DataType           |
|------------------------|-------------------------|--------------------|
| `ticket_number`        | Ticket number           | Text               |
| `issue_date`           | Issue date              | Floating Timestamp |
| `issue_time`           | Issue time              | Number             |
| `meter_id`             | Meter ID                | Text               |
| `marked_time`          | Marked time             | Text               |
| `rp_state_plate`       | State plate registered  | Text               |
| `plate_expiry_date`    | Plate expiry date       | Text               |
| `vin`                  | Vehicle Identification Number | Text        |
| `make`                 | Vehicle make            | Text               |
| `body_style`           | Body style              | Text               |
| `color`                | Color                   | Text               |
| `location`             | Location                | Text               |
| `route`                | Route                   | Text               |
| `agency`               | Agency                  | Number             |
| `violation_code`       | Violation code          | Text               |
| `violation_description`| Violation description   | Text               |
| `fine_amount`          | Fine amount             | Number             |
| `agency_desc`          | Agency description      | Text               |
| `color_desc`           | Color description       | Text               |
| `body_style_desc`      | Body style description  | Text               |
| `loc_lat`              | Latitude                | Number             |
| `loc_long`             | Longitude               | Number             |
| `geolocation`          | Geolocation             | Point              |


## Project Overview
This project explores the parking ticket data provided by the [ City of Los Angeles API, powered by Socrata](https://data.lacity.org/). The goal is to demonstrate ETL with various DB, how to retrieve, process, and serve this data using Python web frameworks: Flask and FastAPI. This comparison focuses on understanding the performance, ease of use, and feature sets provided by different databases and frameworks.

### Technologies Used
- Python 3
- DuckDB
- Flask
- FastAPI
- Requests library
- Jinja2 (for Flask templates)
- Uvicorn (ASGI server for FastAPI)

## Using DuckDB with Parking Ticket Data

In this project, DuckDB, an embedded SQL OLAP database, was utilized to efficiently manage and query a dataset of parking ticket data. DuckDB's unique capabilities allowed for both in-memory and on-disk data management, providing flexibility in data processing and analysis.

### Key Features

- **Storage Modes**: Configured for both rapid in-memory operation and durable on-disk storage.
- **Schema Implementation**: Custom schema applied to accommodate data attributes such as `issue_date`, `fine_amount`, and `location`.
- **Efficient Querying**: Structured queries enabled detailed analysis and report generation, supported by DuckDB's columnar storage and optimized execution.

### Benefits

- **Performance**: Accelerated data operations ideal for analytical tasks.
- **Ease of Use**: Simple integration with Python for straightforward project implementation.
- **Adaptability**: Supports varying scenarios with in-memory and persistent storage options.
