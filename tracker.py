import os
import csv
import re
import json
import js2py
from bs4 import BeautifulSoup
import requests

def scrape_tracksino_table():
    csv_file = "crazytime_master_history.csv"
    url = "https://tracksino.com"
    headers_csv = ["Time", "Dealer", "Multiplier", "Result", "Total_Winners", "Total_Payout"]
    
    # Initialize the tracking file layout explicitly if it is missing
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
        soup = BeautifulSoup(html, 'html.parser')
        
        # ADVANCED FIX: Locate the hidden Nuxt/Next JavaScript state pipeline variables
        js_data_text = None
        for script in soup.find_all('script'):
            script_content = script.string or ""
            if "window.__INITIAL_STATE__" in script_content or "spinHistory" in script_content:
                js_data_text = script_content
                break
        
        if js_data_text:
            try:
                print("🧠 Executing embedded JavaScript context to decode spin array...")
                # Isolate the exact assignment text block cleanly
                js_context = js_data_text.strip()
                if "window.__INITIAL_STATE__ =" in js_context:
                    # Execute the JavaScript string block inside Python to build a matching data object
                    context = js2py.EvalJs()
                    context.execute(js_context)
                    initial_state = context.window.__INITIAL_STATE__.to_dict()
                    
                    # Dig through data dictionaries for matching lists recursively
                    def find_spin_list(obj):
                        if isinstance(obj, list) and len(obj) > 0 and isinstance(obj[0], dict) and ('result' in obj[0] or 'dealer' in obj[0]):
                            return obj
                        if isinstance(obj, dict):
                            for k, v in obj.items():
                                res = find_spin_list(v)
                                if res: return res
                        return None
                    
                    records = find_spin_list(initial_state) or []
                    
                    for item in records:
                        time_val = item.get('time') or item.get('created_at') or item.get('watched_at') or item.get('date') or ''
                        dealer_val = item.get('dealer_name') or item.get('dealer') or 'Unknown'
                        mult_val = item.get('multiplier') or item.get('slot_multiplier') or '1x'
                        res_val = item.get('result') or item.get('wheel_result') or item.get('outcome') or ''
                        win_val = item.get('total_winners') or item.get('winners') or '0'
                        pay_val = item.get('total_payout') or item.get('payout') or '$0'
                        
                        if time_val and res_val:
                            spins_data.append({
                                "Time": str(time_val),
                                "Dealer": str(dealer_val),
                                "Multiplier": str(mult_val),
                                "Result": str(res_val),
                                "Total_Winners": str(win_val),
                                "Total_Payout": str(pay_val)
                            })
            except Exception as js_err:
                print(f"⚠️ JavaScript decoder bypass skipped: {js_err}")

        # HTML GRID FALLBACK: Pulls standard HTML table elements if JavaScript state variables shift
        if not spins_data:
            print("🔄 JavaScript variables absent. Running plain table scan...")
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

        # Deduplication filtering matching logic
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
