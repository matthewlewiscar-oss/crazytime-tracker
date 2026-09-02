import os
import csv
import re
import json
from bs4 import BeautifulSoup
import requests

def scrape_tracksino_table():
    csv_file = "crazytime_master_history.csv"
    debug_file = "debug_view.html"
    url = "https://www.tracksino.com/crazytime"
    headers_csv = ["Time", "Dealer", "Multiplier", "Result", "Total_Winners", "Total_Payout"]
    
    # Initialize the template file layout if missing
    file_exists = os.path.exists(csv_file) and os.path.getsize(csv_file) > 0
    if not file_exists:
        with open(csv_file, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers_csv)
            writer.writeheader()
        file_exists = True

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    print("🚀 Connecting to Tracksino cloud interface...")
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code != 200:
            print(f"❌ Connection failed: {response.status_code}")
            return
            
        html = response.text
        spins_data = []
        
        # 1. Broadest text-search strategy: Hunt for any mention of common dealer/game variables
        soup = BeautifulSoup(html, 'html.parser')
        for table in soup.find_all('table'):
            table_text = table.text.lower()
            if "dealer" in table_text or "history" in table_text or "payout" in table_text:
                for row in table.find_all('tr')[1:]:
                    cols = row.find_all(['td', 'th'])
                    if len(cols) >= 4:
                        texts = [c.text.strip() for c in cols]
                        spins_data.append({
                            "Time": texts[0] if len(texts) > 0 else "N/A",
                            "Dealer": texts[1] if len(texts) > 1 else "N/A",
                            "Multiplier": texts[2] if len(texts) > 2 else "1x",
                            "Result": texts[3] if len(texts) > 3 else "N/A",
                            "Total_Winners": texts[4] if len(texts) > 4 else "0",
                            "Total_Payout": texts[5] if len(texts) > 5 else "$0"
                        })
                break

        # 2. DIAGNOSTIC SAFEGUARD: If no data rows can be found, save the raw page into the repository
        if not spins_data:
            print(f"⚠️ No rows parsed. Saving raw cloud source layout to '{debug_file}' for audit...")
            with open(debug_file, mode="w", encoding="utf-8") as df:
                df.write(html)
            
            # Create a mock entry to force Git to push the debug file updates
            spins_data.append({
                "Time": "DIAGNOSTIC_RUN",
                "Dealer": "CHECK_DEBUG_HTML_FILE",
                "Multiplier": "N/A",
                "Result": "NO_DATA_FOUND",
                "Total_Winners": "0",
                "Total_Payout": "$0"
            })

        # Standard file writing and save module
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
            print(f"🎉 Process completed successfully.")
            
    except Exception as e:
        print(f"❌ Tracking system exception error: {e}")

if __name__ == "__main__":
    scrape_tracksino_table()
