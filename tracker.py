import os
import csv
import re
import json
from bs4 import BeautifulSoup
import requests

def scrape_tracksino_table():
    csv_file = "crazytime_master_history.csv"
    url = "https://tracksino.com"
    headers_csv = ["Time", "Dealer", "Multiplier", "Result", "Total_Winners", "Total_Payout"]
    
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
    
    print("🚀 Extracting dataset from deep background scripts...")
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code != 200:
            print(f"❌ Connection failed: {response.status_code}")
            return
            
        html = response.text
        spins_data = []
        
        # FIX: Scan the massive 177KB file for raw JSON string dumps matching game keys
        # This completely ignores all the messy SVG graphic layout rows completely!
        matches = re.findall(r'(\{[\s\S]*?\})', html)
        for segment in matches:
            if "dealer_name" in segment or "wheel_result" in segment or "slot_multiplier" in segment:
                try:
                    # Clean brackets and isolate matching dictionary entries
                    clean_segment = segment.strip()
                    if not clean_segment.startswith('{'):
                        continue
                    item = json.loads(clean_segment)
                    
                    time_val = item.get('time') or item.get('created_at') or item.get('watched_at') or item.get('date') or ''
                    dealer_val = item.get('dealer_name') or item.get('dealer') or 'Unknown'
                    mult_val = item.get('multiplier') or item.get('slot_multiplier') or '1x'
                    res_val = item.get('result') or item.get('wheel_result') or item.get('outcome') or ''
                    win_val = item.get('total_winners') or item.get('winners') or '0'
                    pay_val = item.get('total_payout') or item.get('payout') or '$0'
                    
                    if time_val and res_val and len(str(res_val)) < 30:
                        spins_data.append({
                            "Time": str(time_val),
                            "Dealer": str(dealer_val),
                            "Multiplier": str(mult_val),
                            "Result": str(res_val),
                            "Total_Winners": str(win_val),
                            "Total_Payout": str(pay_val)
                        })
                except:
                    continue

        # ULTIMATE REGULAR EXPRESSION FALLBACK: 
        # If the web app maps keys inside an complex custom list format, scan raw quotes directly
        if not spins_data:
            print("🔄 Running pattern scanner on raw text blocks...")
            # Capture strings matching typical round logs: e.g., "14:35", "DealerName", "Crazy Time"
            raw_spins = re.findall(r'("time":"[^"]+","dealer_name":"[^"]+","slot_multiplier":"[^"]+","wheel_result":"[^"]+")', html)
            for raw_spin in raw_spins:
                try:
                    item = json.loads("{" + raw_spin + "}")
                    spins_data.append({
                        "Time": item.get('time', ''),
                        "Dealer": item.get('dealer_name', 'Unknown'),
                        "Multiplier": item.get('slot_multiplier', '1x'),
                        "Result": item.get('wheel_result', ''),
                        "Total_Winners": "0",
                        "Total_Payout": "$0"
                    })
                except:
                    continue

        if not spins_data:
            print("❌ No matching spin rows could be unsealed from the layout.")
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
        print(f"❌ Tracking system exception error: {e}")

if __name__ == "__main__":
    scrape_tracksino_table()
