import os
import csv
import re
from bs4 import BeautifulSoup
import requests

def scrape_tracksino_table():
    csv_file = "crazytime_master_history.csv"
    
    # NEW INTERFACE TARGET: Targets the public tracking matrix directly 
    url = "https://tracksino.com"
    headers_csv = ["Time", "Dealer", "Multiplier", "Result", "Total_Winners", "Total_Payout"]
    
    # Clean out diagnostic error alerts from previous test runs cleanly if found
    file_exists = os.path.exists(csv_file) and os.path.getsize(csv_file) > 0
    if file_exists:
        with open(csv_file, mode="r", encoding="utf-8") as f:
            lines = f.readlines()
        # Wipes file to clear mock diagnostic codes from your spreadsheet log
        if any("DIAGNOSTIC_RUN" in line for line in lines):
            os.remove(csv_file)
            file_exists = False

    if not file_exists:
        with open(csv_file, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers_csv)
            writer.writeheader()
        file_exists = True

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5"
    }
    
    print("🚀 Querying Tracksino public historical data endpoint...")
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code != 200:
            print(f"❌ Target path closed or blocked: {response.status_code}")
            return
            
        print("✅ Data feed downloaded successfully! Unpacking spin log metrics...")
        soup = BeautifulSoup(response.text, 'html.parser')
        spins_data = []
        
        # Look across the interface container elements for row grids
        for table in soup.find_all('table'):
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all(['td', 'th'])
                if len(cols) >= 4:
                    texts = [c.text.strip() for c in cols]
                    
                    # Ignore title headers if they match text strings
                    if "time" in texts[0].lower() or "dealer" in texts[0].lower():
                        continue
                        
                    spins_data.append({
                        "Time": texts[0],
                        "Dealer": texts[1] if len(texts) > 1 else "Unknown",
                        "Multiplier": texts[2] if len(texts) > 2 else "1x",
                        "Result": texts[3] if len(texts) > 3 else "N/A",
                        "Total_Winners": texts[4] if len(texts) > 4 else "0",
                        "Total_Payout": texts[5] if len(texts) > 5 else "$0"
                    })
            if spins_data:
                break

        if not spins_data:
            print("❌ No matching spin rows could be isolated from this endpoint variant.")
            return

        existing_timestamps = set()
        with open(csv_file, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames and "Time" in reader.fieldnames:
                for r in reader:
                    existing_timestamps.add(r["Time"])

        new_spins = [spin for spin in spins_data if spin["Time"] not in existing_timestamps]

        if new_spins:
            with open(csv_file, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=headers_csv)
                writer.writerows(new_spins)
            print(f"🎉 Success! Extracted and saved {len(new_spins)} new unique live spins.")
        else:
            print("✅ No new spins discovered. Database spreadsheet remains fully up to date.")

    except Exception as e:
        print(f"❌ Extraction error: {e}")

if __name__ == "__main__":
    scrape_tracksino_table()
