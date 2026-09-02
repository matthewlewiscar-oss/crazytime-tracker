import os
import sys
import time
import csv
import requests


def scrape_crazytime_history():
    csv_file = "crazytime_master_history.csv"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://tracksino.com",
        "Referer": "https://tracksino.com/",
    }

    page = 1
    per_page = 100
    all_spins = []

    print("Fetching daily data from Tracksino...")

    while True:
        api_url = (
            "https://api.tracksino.com/crazytime_history"
            f"?filter=&page_num={page}&per_page={per_page}"
            "&period=24hours&table_id=8&sort_by=&sort_desc=false"
        )
        try:
            response = requests.get(api_url, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"Bad response: {response.status_code} for {api_url}")
                break

            result = response.json()

            # The API may return either a bare list of spins, or an object
            # wrapping the list under a "data" key. Handle both.
            if isinstance(result, list):
                spin_batch = result
            elif isinstance(result, dict):
                spin_batch = result.get("data", [])
            else:
                spin_batch = []

            if not spin_batch:
                break

            all_spins.extend(spin_batch)

            # Stop once a page comes back with fewer than per_page items
            # (means we've reached the end of the data).
            if len(spin_batch) < per_page:
                break

            page += 1
            time.sleep(1)
        except Exception as e:
            print(f"Error: {e}")
            break

    if not all_spins:
        print("No data harvested.")
        sys.exit(1)  # fail loudly so GitHub Actions marks this step red

    # Load existing round codes to avoid saving duplicates.
    # Tracksino uses "round_code" as the unique identifier per spin (there's
    # no "id" field in the response).
    unique_key = "round_code"
    existing_ids = set()
    file_exists = os.path.exists(csv_file) and os.path.getsize(csv_file) > 0

    if file_exists:
        with open(csv_file, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames and unique_key in reader.fieldnames:
                for row in reader:
                    existing_ids.add(str(row[unique_key]))

    # Filter out spins we already have stored
    new_spins = [
        spin
        for spin in all_spins
        if str(spin.get(unique_key, "")) not in existing_ids
    ]

    if new_spins:
        headers_csv = list(new_spins[0].keys())

        with open(csv_file, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers_csv)
            if not file_exists:
                writer.writeheader()
            writer.writerows(new_spins)
        print(f"Success! Added {len(new_spins)} new unique spins to the master log.")
    else:
        print("No new spins found. Database is already up to date.")


if __name__ == "__main__":
    scrape_crazytime_history()
