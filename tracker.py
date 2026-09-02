import os
import time
import csv
import requests

def scrape_crazytime_history():
    csv_file = "crazytime_master_history.csv"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://tracksino.com",
        "Referer": "https://tracksino.com/"
    }
    
    page = 1
    all_spins = []
    
    print("🚀 Fetching daily data from Tracksino...")
    
    while True:
        api_url = f"https://tracksino.com{page}&per_page=100&period=24hours"
        try:
            response = requests.get(api_url, headers=headers, timeout=10)
            if response.status_code != 200:
                break
                
            result = response.json()
            spin_batch = result.get("data", [])
            if not spin_batch:
                break
                
            all_spins.extend(spin_batch)
            page += 1
            time.sleep(1) 
        except Exception as e:
            print(f"❌ Error: {e}")
            break

    if not all_spins:
        print("❌ No data harvested.")
        return

    # Load existing IDs to avoid saving duplicates
    existing_ids = set()
    file_exists = os.path.exists(csv_file) and os.path.getsize(csv_file) > 0
    
    if file_exists:
        with open(csv_file, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames and 'id' in reader.fieldnames:
                for row in reader:
                    existing_ids.add(str(row['id']))

    # Filter out spins we already have stored
    new_spins = [spin for spin in all_spins if str(spin.get('id', '')) not in existing_ids]
    
    if new_spins:
        # FIXED LINE: Grabs the keys from the very first data entry dictionary safely
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
