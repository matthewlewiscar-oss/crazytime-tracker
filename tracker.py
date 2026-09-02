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
    
    # Initialize the spreadsheet template layout file cleanly if missing
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
        soup = BeautifulSoup(html, 'html.parser')
        
        # FIX: Find ALL script blocks and look for raw spin data objects wherever they are hidden
        for script in soup.find_all('script'):
            if script.string and ("dealer_name" in script.string or "wheel_result" in script.string or "spin-history" in script.string.lower()):
                try:
                    # Clean up the JavaScript variable wrapper to isolate raw data text text
                    clean_text = script.string.strip()
                    if "window.__INITIAL_STATE__ =" in clean_text:
                        clean_text = clean_text.split("window.__INITIAL_STATE__ =", 1)[1].rsplit(";", 1)[0].strip()
                    elif "id=" in str(script):
                        clean_text = clean_text
                        
                    raw_json = json.loads(clean_text)
                    
                    # Dig through any inner nested layer names dynamically
                    records = []
                    if isinstance(raw_json, list):
                        records = raw_json
                    elif isinstance(raw_json, dict):
                        for k, v in raw_json.items():
                            if isinstance(v, list):
                                records = v
                                break
                            elif isinstance(v, dict) and "data" in v:
                                records = v["data"]
                                break
                        if not records:
                            records = raw_json.get('data', raw_json.get('spins', raw_json.get('history', [])))
                    
                    for item in records:
                        if isinstance(item, dict):
                            # Map out alternative dictionary key variants used by regional endpoints
                            time_val = item.get('time') or item.get('created_at') or item.get('watched_at') or item.get('date') or ''
                            dealer_val = item.get('dealer_name') or item.get('dealer') or item.get('dealer_id') or 'Unknown'
                            mult_val = item.get('multiplier') or item.get('slot_multiplier') or item.get('top_slot_multiplier') or '1x'
                            res_val = item.get('result') or item.get('wheel_result') or item.get('outcome') or ''
                            win_val = item.get('total_winners') or item.get('winners') or item.get('winner_count') or '0'
                            pay_val = item.get('total_payout') or item.get('payout') or item.get('amount') or '$0'
                            
                            if time_val and res_val:
                                spins_data.append({
                                    "Time": str(time_val),
                                    "Dealer": str(dealer_val),
                                    "Multiplier": str(mult_val),
                                    "Result": str(res_val),
                                    "Total_Winners": str(win_val),
                                    "Total_Payout": str(pay_val)
                                })
                except Exception as json_err:
                    continue

        # FALLBACK TABLE SELECTOR: Scrapes HTML grid rows if JavaScript strings are absent
        if not spins_data:
            print("🔄 Text strings missing. Running table fallback layout check...")
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

        # Deduplication matching row check filters
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
