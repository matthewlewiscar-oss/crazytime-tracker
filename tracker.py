import os
import csv
import re
from bs4 import BeautifulSoup
import requests

def scrape_tracksino_table():
    csv_file = "crazytime_master_history.csv"
    url = "https://tracksino.com"
    headers_csv = ["Time", "Dealer", "Multiplier", "Result", "Total_Winners", "Total_Payout"]
    
    # Force initialize the spreadsheet layout if missing
    file_exists = os.path.exists(csv_file) and os.path.getsize(csv_file) > 0
    if not file_exists:
        with open(csv_file, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers_csv)
            writer.writeheader()
        file_exists = True

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    print("🚀 Connecting directly to Tracksino web interface...")
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code != 200:
            print(f"❌ Connection failed: {response.status_code}")
            return
            
        print("✅ Connected successfully! Finding data rows...")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # FIX: Find ANY grid container or table containing historical spins
        table = soup.find('table')
        if not table:
            table = soup.find(class_=re.compile(r"table|history|spin|log", re.IGNORECASE))
            
        if not table:
            print("❌ Could not isolate the display container.")
            return
            
        spins_data = []
        
        # FIX: Dynamically find table rows or generic grid container elements
        rows = table.find_all('tr') if table.name == 'table' else table.find_all(class_=re.compile(r"row|item", re.IGNORECASE))
        
        for row in rows:
            cols = row.find_all(['td', 'th']) if table.name == 'table' else row.find_all(recursive=False)
            if not cols or len(cols) < 4:
                continue
                
            # Extract safe cell values by filtering array positions dynamically
            texts = [c.text.strip() for c in cols if c.text.strip() != ""]
            if len(texts) < 4:
                continue
                
            row_data = {
                "Time": texts[0],
                "Dealer": texts[1] if len(texts) > 1 else "",
                "Multiplier": texts[2] if len(texts) > 2 else "",
                "Result": texts[3] if len(texts) > 3 else "",
                "Total_Winners": texts[4] if len(texts) > 4 else "0",
                "Total_Payout": texts[5] if len(texts) > 5 else "$0"
            }
            # Skip the table header if it got caught by filtering keywords
            if row_data["Time"].lower() in ["time", "date", "timestamp"]:
                continue
                
            spins_data.append(row_data)

        if not spins_data:
            print("❌ No text rows were harvested inside the table object.")
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
        print(f"❌ Tracking error: {e}")

if __name__ == "__main__":
    scrape_tracksino_table()
