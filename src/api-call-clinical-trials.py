#2025-02-19-upwork-clintrials-api-v1.1
#Below is a first pass at a Python script that will:
#   •   Query the ClinicalTrials.gov API for studies with a “StudyFirstPostDate” in the last 7 days (using the date range February 12–19, 2025).
#   •   Loop through pages (using the nextPageToken).
#   •   For each study, extract the NCT ID and store the full JSON record in a SQLite table.

#Before we run it, please let me know:
#   •   Storage Format: JSON blob
#   •   Page Size: I’ve set the page size to 100



# --- Imports ----

import requests
import sqlite3
import json
from datetime import datetime, timedelta

# --- Configuration ---

# For testing, we assume "today" is February 19, 2025.

########### CHANGE TO TODAY'S DATE

today = datetime.today()
start_date = today - timedelta(days=7)  # last 7 days
start_date_str = start_date.strftime('%Y-%m-%d')
end_date_str = today.strftime('%Y-%m-%d')

# Build the query term using Essie expression syntax for StudyFirstPostDate
query_term = f"AREA[StudyFirstPostDate]RANGE[{start_date_str},{end_date_str}]"

# API endpoint and parameters
api_url = "https://clinicaltrials.gov/api/v2/studies"
params = {
    "format": "json",
    "query.term": query_term,
    "pageSize": 100  # Adjust if needed
    # "pageToken" will be added dynamically
}

# --- Set up SQLite database ---
db_name = "data/clinical-trials-api.db"
conn = sqlite3.connect(db_name)
cursor = conn.cursor()

# Create a table to store studies.
# Here we store the NCT ID and the full JSON blob.
cursor.execute('''
CREATE TABLE IF NOT EXISTS studies (
    nct_id TEXT PRIMARY KEY,
    json_data TEXT
)
''')
conn.commit()

# --- Function to fetch and store studies ---
def fetch_and_store_studies():
    total_inserted = 0
    pageToken = None

    while True:
        # Update parameters with the pageToken if available
        if pageToken:
            params["pageToken"] = pageToken
        else:
            params.pop("pageToken", None)

        print("Requesting page with parameters:")
        print(params)
        response = requests.get(api_url, params=params)
        if response.status_code != 200:
            print("Error fetching data:", response.text)
            break

        data = response.json()
        studies = data.get("studies", [])
        if not studies:
            print("No studies found on this page.")
            break

        for study in studies:
            # Extract the NCT ID from the nested structure
            try:
                nct_id = study["protocolSection"]["identificationModule"]["nctId"]
            except KeyError:
                print("A study without an NCT ID was encountered; skipping.")
                continue

            # Store the full JSON as a string
            json_text = json.dumps(study)
            try:
                cursor.execute(
                    "INSERT OR REPLACE INTO studies (nct_id, json_data) VALUES (?, ?)",
                    (nct_id, json_text)
                )
                total_inserted += 1
            except sqlite3.Error as e:
                print("SQLite error:", e)
        conn.commit()

        # Check if there is a next page
        pageToken = data.get("nextPageToken")
        if not pageToken:
            print("No nextPageToken; reached last page.")
            break

    print(f"Inserted {total_inserted} studies into {db_name}.")

# --- Run the fetching process ---
if __name__ == "__main__":
    fetch_and_store_studies()
    conn.close()