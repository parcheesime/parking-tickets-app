import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import requests
import logging
from config import get_api_token, CONNECTION_STRING_Neon

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# Define PostgreSQL connection
DB_CONNECTION_STRING = CONNECTION_STRING_Neon

# Define PostgreSQL Schema (without marked_time and agency_desc)
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


def ping_api(api_url):
    """Ping API to check if it's reachable."""
    try:
        response = requests.get(api_url, timeout=5)
        if response.status_code == 200:
            logging.info("API is reachable.")
            return True
        else:
            logging.error(f"API ping failed with status code {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logging.error(f"API ping failed: {e}")
        return False


def fetch_data(api_url, headers):
    """Fetch data from API."""
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        logging.info("Data successfully fetched from API.")
        return response.json()
    else:
        logging.error(f"API request failed with status code {response.status_code}")
        return []  # Return empty list if API call fails


def convert_plate_expiry(date_str):
    """Convert YYYYMM to YYYY-MM-01 format. Handle '0' values."""
    try:
        if date_str is None or str(date_str) == "0" or pd.isna(date_str):
            return "1900-01-01"  # Default value for missing expiry dates
        return pd.to_datetime(date_str, format="%Y%m").strftime("%Y-%m-01")
    except ValueError:
        logging.error(f"Invalid plate_expiry_date format: {date_str}")
        return "1900-01-01"  # Assign default date if conversion fails


def convert_time(time_str):
    """Convert HHMM format to HH:MM:SS format for PostgreSQL TIME type."""
    try:
        time_str = str(int(float(time_str))).zfill(4)  # Ensure 4 characters (e.g., '845' -> '0845')
        return pd.to_datetime(time_str, format="%H%M").strftime("%H:%M:%S")
    except (ValueError, TypeError):
        logging.error(f"Invalid time format: {time_str}")
        return None  # Store as NULL if conversion fails


def clean_dataframe(df):
    """Clean and transform the DataFrame for PostgreSQL insertion."""
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

    # Transform data
    df["plate_expiry_date"] = df["plate_expiry_date"].apply(convert_plate_expiry)
    df["issue_time"] = df["issue_time"].apply(convert_time)

    # Handle missing values
    df["make"] = df["make"].fillna("Unknown")
    df["body_style"] = df["body_style"].fillna("Unknown")
    df["color"] = df["color"].fillna("Unknown")
    df["violation_code"] = df["violation_code"].fillna("Unknown")

    df["fine_amount"] = df["fine_amount"].fillna(0)
    df["loc_lat"] = df["loc_lat"].fillna(0)
    df["loc_long"] = df["loc_long"].fillna(0)

    df = df.where(pd.notnull(df), None)  # Convert missing values to None for PostgreSQL

    logging.info(f"Cleaned DataFrame shape: {df.shape}")
    return df


def setup_database(connection_string):
    """Drop and recreate the PostgreSQL table."""
    try:
        conn = psycopg2.connect(connection_string)
        cursor = conn.cursor()
        cursor.execute(CREATE_TABLE_QUERY)
        conn.commit()
        logging.info("Table 'parking_tickets' dropped and recreated successfully.")
    except Exception as e:
        logging.error(f"Error setting up database: {e}")
    finally:
        cursor.close()
        conn.close()


def insert_data_into_postgres(df, connection_string):
    """Insert cleaned data into PostgreSQL."""
    if df.empty:
        logging.warning("No valid data to insert. Skipping database insertion.")
        return

    data_tuples = [tuple(x) for x in df.to_numpy()]

    # PostgreSQL insert query (without marked_time and agency_desc)
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
        logging.info("Data successfully inserted into PostgreSQL.")
    except Exception as e:
        logging.error(f"Database insertion error: {e}")
    finally:
        cursor.close()
        conn.close()


def main():
    """Main execution function."""
    API_URL = "https://data.lacity.org/resource/4f5p-udkv.json"
    headers = {
        "Accept": "application/json",
        "X-App-Token": get_api_token()
    }

    # Ping API before fetching data
    if not ping_api(API_URL):
        logging.error("API is unreachable. Exiting script.")
        return

    # Fetch data from API
    data = fetch_data(API_URL, headers)

    # Load data into Pandas DataFrame
    df = pd.DataFrame(data)

    # Clean the data
    df = clean_dataframe(df)

    # Drop & recreate table
    setup_database(DB_CONNECTION_STRING)

    # Insert into PostgreSQL (Neon DB)
    insert_data_into_postgres(df, DB_CONNECTION_STRING)


if __name__ == "__main__":
    main()