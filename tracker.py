import os
import csv
import re
import json
from bs4 import BeautifulSoup
import requests

def scrape_tracksino_table():
    csv_file = "crazytime_master_history.csv"
    url = "https://www.tracksino.com/crazytime"
    headers_csv = ["Time", "Dealer", "Multiplier", "Result", "Total_Winners", "Total_Payout"]
    
    # Initialize the spreadsheet template if it is empty
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
            print(f"❌ Connection closed: {response.status_code}")
            return
            
        html = response.text
        spins_data = []
        
        # FIX: Look for raw pre-rendered JSON string arrays embedded inside the page scripts
        # This completely skips hunting for unstable HTML <table> tags
        json_match = re.search(r'id="spin-history-data"[^>]*>([\s\S]*?)</script>', html)
        
        if json_match:
            try:
                raw_data = json.loads(json_match.group(1).strip())
                # Normalize data array lists if kept inside an inner key dictionary wrapper
                records = raw_data if isinstance(raw_data, list) else raw_data.get('data', [])
                
                for item in records:
                    spins_data.append({
                        "Time": str(item.get('time', item.get('created_at', ''))),
                        "Dealer": str(item.get('dealer_name', item.get('dealer', ''))),
                        "Multiplier": str(item.get('multiplier', item.get('slot_multiplier', '1x'))),
                        "Result": str(item.get('result', item.get('wheel_result', ''))),
                        "Total_Winners": str(item.get('total_winners', item.get('winners', '0'))),
                        "Total_Payout": str(item.get('total_payout', item.get('payout', '$0')))
                    })
            except Exception as json_err:
                print(f"⚠️ JSON tracking variant skipped: {json_err}")

        # FALLBACK BACKUP: If the script cannot locate text blocks, harvest standard cell components cleanly
        if not spins_data:
            print("🔄 JSON container absent. Initiating structural layout scan fallback...")
            soup = BeautifulSoup(html, 'html.parser')
            for table in soup.find_all('table'):
                table_text = table.text.lower()
                if "dealer" in table_text or "history" in table_text or "payout" in table_text:
                    for row in table.find_all('tr')[1:]:
                        cols = row.find_all(['td', 'th'])
                        if len(cols) >= 6:
                            spins_data.append({
                                "Time": cols[0].text.strip(),
                                "Dealer": cols[1].text.strip(),
                                "Multiplier": cols[2].text.strip(),
                                "Result": cols[3].text.strip(),
                                "Total_Winners": cols[4].text.strip(),
                                "Total_Payout": cols[5].text.strip()
                            })
                    break

        if not spins_data:
            print("❌ No matching spin rows could be parsed from the layout structure.")
            return

        # Deduplication layout matching processing
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
            print("✅ No new spins discovered. Database remains fully up to date.")

    except Exception as e:
        print(f"❌ Tracking system exception error: {e}")

if __name__ == "__main__":
    scrape_tracksino_table()
