import os
import csv
import time
from bs4 import BeautifulSoup
import requests

def scrape_tracksino_table():
    csv_file = "crazytime_master_history.csv"
    url = "https://tracksino.com"
    
    # Standard desktop user signature
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    print("🚀 Connecting directly to Tracksino web interface...")
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        
        if response.status_code != 200:
            print(f"❌ Connection closed by server. Code: {response.status_code}")
            return
            
        print("✅ Connected successfully! Reading visual data rows...")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        table = soup.find('table')
        if not table:
            print("❌ Could not isolate the display table container.")
            return
            
        spins_data = []
        rows = table.find_all('tr')
        
        for row in rows[1:]:
            cols = row.find_all(['td', 'th'])
            if not cols:
                continue
                
            row_data = {
                "Time": cols[0].text.strip() if len(cols) > 0 else "",
                "Dealer": cols[1].text.strip() if len(cols) > 1 else "",
                "Multiplier": cols[2].text.strip() if len(cols) > 2 else "",
                "Result": cols[3].text.strip() if len(cols) > 3 else "",
                "Total_Winners": cols[4].text.strip() if len(cols) > 4 else "",
                "Total_Payout": cols[5].text.strip() if len(cols) > 5 else ""
            }
            spins_data.append(row_data)

        if not spins_data:
            print("❌ No text rows were harvested inside the table object.")
            return

        file_exists = os.path.exists(csv_file) and os.path.getsize(csv_file) > 0
        existing_timestamps = set()

        if file_exists:
            with open(csv_file, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames and "Time" in reader.fieldnames:
                    for r in reader:
                        existing_timestamps.add(r["Time"])

        new_spins = [spin for spin in spins_data if spin["Time"] not in existing_timestamps]

        if new_spins:
            headers_csv = ["Time", "Dealer", "Multiplier", "Result", "Total_Winners", "Total_Payout"]
            with open(csv_file, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=headers_csv)
                if not file_exists:
                    writer.writeheader()
                writer.writerows(new_spins)
            print(f"🎉 Success! Extracted and saved {len(new_spins)} new unique live spins.")
        else:
            print("✅ No new spins discovered. Database spreadsheet remains fully up to date.")

    except Exception as e:
        print(f"❌ Tracking error: {e}")

if __name__ == "__main__":
    scrape_tracksino_table()
