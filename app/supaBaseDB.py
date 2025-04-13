import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import requests
import logging
from config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME, get_api_token

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# Define pagination parameters
LIMIT = 50000  # Fetch 50,000 records per request
OFFSET = 0  # Start at 0


# Define PostgreSQL Schema
CREATE_TABLE_QUERY = """
DROP TABLE IF EXISTS parking_tickets;
CREATE TABLE parking_tickets (
    ticket_number TEXT PRIMARY KEY,
    issue_date DATE NOT NULL,
    issue_time TIME NOT NULL,
    rp_state_plate TEXT,
    plate_expiry_date DATE,
    make TEXT,  
    body_style TEXT,  
    color TEXT,  
    location TEXT NOT NULL,
    agency TEXT NOT NULL,
    violation_code TEXT NOT NULL,
    fine_amount NUMERIC NOT NULL,
    loc_lat NUMERIC NOT NULL,
    loc_long NUMERIC NOT NULL
);
"""


def fetch_data(api_url, headers, limit, offset):
    """Fetch paginated data from API."""
    params = {
        "$limit": limit,
        "$offset": offset
    }
    response = requests.get(api_url, headers=headers, params=params)
    
    if response.status_code == 200:
        logging.info(f"Fetched {limit} records starting from offset {offset}.")
        return response.json()
    else:
        logging.error(f"API request failed with status code {response.status_code}")
        return []  # Return empty list if API fails


def convert_plate_expiry(date_str):
    """Convert YYYYMM to YYYY-MM-01 format. Handle '0' values."""
    try:
        if date_str == "0" or pd.isna(date_str):  # Handle invalid values
            return None  # Store as NULL in PostgreSQL
        return pd.to_datetime(date_str, format="%Y%m").strftime("%Y-%m-01")
    except ValueError:
        logging.error(f"Invalid plate_expiry_date format: {date_str}")
        return None  # Return None if conversion fails


def convert_time(time_str):
    """Convert HHMM format to HH:MM:SS for PostgreSQL TIME type."""
    try:
        time_str = str(time_str).zfill(4)  # Ensure it's at least 4 chars (e.g., '845' -> '0845')
        return pd.to_datetime(time_str, format="%H%M").strftime("%H:%M:%S")
    except (ValueError, TypeError):
        logging.error(f"Invalid time format: {time_str}")
        return None


def clean_dataframe(df):
    """Clean and transform the DataFrame for PostgreSQL insertion, filtering by years."""
    if df.empty:
        logging.warning("Received an empty DataFrame. Skipping processing.")
        return df

    # Columns to keep (without marked_time and agency_desc)
    columns_to_keep = [
        "ticket_number", "issue_date", "issue_time", "rp_state_plate",
        "plate_expiry_date", "make", "body_style", "color", "location", "agency",
        "violation_code", "fine_amount", "loc_lat", "loc_long"
    ]

    df = df.loc[:, [col for col in columns_to_keep if col in df.columns]]

    # Convert issue_date to datetime for filtering
    df["issue_date"] = pd.to_datetime(df["issue_date"], errors="coerce")

    # Filter rows where issue_date is selected
    df = df[df["issue_date"].dt.year.isin([2025, 2024, 2023, 2022, 2021, 2020])]

    # Convert 'plate_expiry_date' from YYYYMM to YYYY-MM-01
    df["plate_expiry_date"] = df["plate_expiry_date"].apply(convert_plate_expiry)
    
    # Convert 'issue_time' to HH:MM:SS format
    df["issue_time"] = df["issue_time"].apply(convert_time)

    # Handle missing values
    df["make"] = df["make"].fillna("Unknown")
    df["body_style"] = df["body_style"].fillna("Unknown")
    df["color"] = df["color"].fillna("Unknown")
    df["violation_code"] = df["violation_code"].fillna("Unknown")

    df["fine_amount"] = df["fine_amount"].fillna(0)
    df["loc_lat"] = df["loc_lat"].fillna(0)
    df["loc_long"] = df["loc_long"].fillna(0)

    df = df.where(pd.notnull(df), None)  # Convert missing values to None

    logging.info(f"Filtered DataFrame shape (only years 2025-2022): {df.shape}")
    return df


def setup_database():
    """Drop and recreate the PostgreSQL table in Supabase."""
    try:
        # Create connection string dynamically
        connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
        
        # Connect to the database
        conn = psycopg2.connect(connection_string)
        
        with conn, conn.cursor() as cursor:
            cursor.execute(CREATE_TABLE_QUERY)
            conn.commit()
        
        logging.info("Table 'parking_tickets' dropped and recreated successfully in Supabase.")
    
    except psycopg2.OperationalError as e:
        logging.error(f"Database connection failed: {e}")
    except Exception as e:
        logging.error(f"Error setting up database: {e}")


def insert_data_into_postgres(df, connection_string):
    """Insert cleaned data into PostgreSQL in batches."""
    if df.empty:
        logging.warning("No valid data to insert. Skipping database insertion.")
        return

    data_tuples = [tuple(x) for x in df.to_numpy()]

    insert_query = """
    INSERT INTO parking_tickets (
        ticket_number, issue_date, issue_time, rp_state_plate, 
        plate_expiry_date, make, body_style, color, location, agency, 
        violation_code, fine_amount, loc_lat, loc_long
    ) VALUES %s
    ON CONFLICT (ticket_number) DO NOTHING;
    """

    try:
        conn = psycopg2.connect(connection_string)
        cursor = conn.cursor()
        execute_values(cursor, insert_query, data_tuples)
        conn.commit()
        logging.info(f"Inserted {len(data_tuples)} records into PostgreSQL.")
    except Exception as e:
        logging.error(f"Database insertion error: {e}")
    finally:
        cursor.close()
        conn.close()


def main():
    """Main execution function."""
    # Ping Los Angelas Parking Data
    API_URL = "https://data.lacity.org/resource/4f5p-udkv.json"
    headers = {
        "Accept": "application/json",
        "X-App-Token": get_api_token()
    }

    # Drop & recreate table
    setup_database(connection_string)

    offset = 0

    while True:
        # Fetch paginated data
        data = fetch_data(API_URL, headers, LIMIT, offset)
        if not data:
            logging.info("No more data to fetch.")
            break

        # Convert to DataFrame & clean
        df = pd.DataFrame(data)
        df = clean_dataframe(df)

        # Insert into PostgreSQL
        insert_data_into_postgres(df, connection_string)

        # Move to next batch
        offset += LIMIT
        logging.info(f"Fetching next batch with offset {offset}...")

    logging.info("All data has been fetched and inserted into PostgreSQL.")


# if __name__ == "__main__":
#     main()


try:
    connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
    conn = psycopg2.connect(connection_string)
    cursor = conn.cursor()
    cursor.execute("SELECT NOW();")
    print("Connected Successfully! Current Time:", cursor.fetchone())
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Failed to connect: {e}")
