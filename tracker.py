import os
import sys
import time
import csv
import requests

def scrape_crazytime_history():
    csv_file = "crazytime_master_history.csv"

    # Expanded browser fingerprints to masquerade as an organic user and bypass 403 walls
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Origin": "https://tracksino.com",
        "Referer": "https://tracksino.com/",
        "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Connection": "keep-alive"
    }

    page = 1
    per_page = 100
    all_spins = []

    print("🚀 Fetching daily data from Tracksino...")

    while True:
        api_url = (
            "https://api.tracksino.com/crazytime_history"
            f"?filter=&page_num={page}&per_page={per_page}"
            "&period=24hours&table_id=8&sort_by=&sort_desc=false"
        )
        try:
            response = requests.get(api_url, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"❌ Bad response: {response.status_code} for {api_url}")
                break

            result = response.json()

            if isinstance(result, list):
                spin_batch = result
            elif isinstance(result, dict):
                spin_batch = result.get("data", [])
            else:
                spin_batch = []

            if not spin_batch:
                break

            all_spins.extend(spin_batch)

            if len(spin_batch) < per_page:
                break

            page += 1
            time.sleep(2) # Increased slightly to prevent overwhelming the remote server
        except Exception as e:
            print(f"❌ Error: {e}")
            break

    if not all_spins:
        print("❌ No data harvested.")
        sys.exit(1)

    # Main structural processing from Claude
    unique_key = "round_code"
    existing_ids = set()
    file_exists = os.path.exists(csv_file) and os.path.getsize(csv_file) > 0

    if file_exists:
        with open(csv_file, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames and unique_key in reader.fieldnames:
                for row in reader:
                    existing_ids.add(str(row[unique_key]))

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
        print(f"🎉 Success! Added {len(new_spins)} new unique spins to the master log.")
    else:
        print("✅ No new spins found. Database is already up to date.")

if __name__ == "__main__":
    scrape_crazytime_history()
