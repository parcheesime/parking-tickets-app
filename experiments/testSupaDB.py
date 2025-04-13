import requests
import logging
from config import DB_URL, DB_API_KEY

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# Supabase API Details
SUPABASE_URL = DB_URL
SUPABASE_API_KEY = DB_API_KEY

# Headers for authentication
headers = {
    "apikey": SUPABASE_API_KEY,
    "Authorization": f"Bearer {SUPABASE_API_KEY}",
    "Content-Type": "application/json"
}


def ping_supabase_db():
    """Ping Supabase to check if the database is reachable."""
    test_url = f"{SUPABASE_URL}/rest/v1/"  # Root endpoint, no table

    try:
        response = requests.get(test_url, headers=headers)
        if response.status_code in [200, 401]:  # 401 means it requires a table, but still reachable
            logging.info("✅ Supabase database is reachable!")
        else:
            logging.error(f"❌ Supabase database ping failed! Status Code: {response.status_code}")
            logging.error(f"Response: {response.text}")
    except Exception as e:
        logging.error(f"❌ Error reaching Supabase database: {e}")


# Run the test
ping_supabase_db()