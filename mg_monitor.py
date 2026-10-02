import time
import threading
import requests
from datetime import datetime
from curl_cffi import requests as cffi_requests

# ==========================================
# KONFIGURASI GLOBAL M&G
# ==========================================
WEBHOOK_URL = "https://discord.com/api/webhooks/1552512118736035971/ezzci7fFs33b-G8RTO1m8vJr9vgCECtxAVFXemVGQAOEn6gj_WY8PldhlHQJd63OFAqC"
API_URL = "https://jkt48.com/api/v1/exclusives/EX24AE/bonus?lang=id"
CHECK_INTERVAL = 60  

TARGET_MEMBERS = [
    "Grace Octaviani", 
    "Michelle Alexandra", 
    "Jazzlyn Trisha", 
    "Fiony Alveria", 
    "Indah Cahya", 
    "Marsha Lenathea", 
    "Nina Tutachia"
]

LATEST_STATUS_MG = {
    "last_check": 0,
    "total_quota": 0,
    "members": []
}

state = {
    "last_sunday_check_date": None,
    "last_monday_update_date": None,
    "last_daily_summary_date": None,
    "initial_sent": False  
}

def get_mg_data():
    return LATEST_STATUS_MG

def fetch_jkt48_api():
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://jkt48.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = cffi_requests.get(API_URL, impersonate="chrome120", headers=headers, timeout=15)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error koneksi API M&G: {e}")
    return None

def update_web_status_mg(api_data):
    global LATEST_STATUS_MG
    parsed_items = []
    
    if not api_data or "data" not in api_data:
        return
        
    for session_obj in api_data["data"]:
        session_name = session_obj.get("label", "-")
        for detail in session_obj.get("session_members", []):
            parsed_items.append({
                "name": detail.get("member_name", "Unknown"),
                "session": session_name,
                "track": detail.get("label", "-"),
                "quota": int(detail.get("available_quota", 0))
            })
            
    LATEST_STATUS_MG["last_check"] = time.time()
    LATEST_STATUS_MG["members"] = parsed_items
    LATEST_STATUS_MG["total_quota"] = sum(m["quota"] for m in parsed_items)

def process_member_quotas(api_data):
    member_status = {}
    if not api_data or "data" not in api_data: return member_status

    for session in api_data["data"]:
        session_label = session.get("label", "Unknown Sesi")
        for member in session.get("session_members", []):
            name = member.get("member_name", "Unknown")
            quota = int(member.get("available_quota", 0))
            lane = member.get("label", "-") 
            
            if name not in member_status:
                member_status[name] = {"total_quota": 0, "available_sessions": []}
            
            member_status[name]["total_quota"] += quota
            if quota > 0:
                member_status[name]["available_sessions"].append(f"{session_label}\n   ↳ {lane} ({quota} tiket)")
            
    return dict(sorted(member_status.items(), key=lambda item: item[1]["total_quota"], reverse=True))

def monitor_worker():
    print("Mulai memonitor API JKT48 M&G...")
    while True:
        now = datetime.now()
        api_data = fetch_jkt48_api()
        
        if api_data:
            update_web_status_mg(api_data)
            member_status = process_member_quotas(api_data)
            # Notifikasi tambahan Discord Anda bisa dipanggil di sini jika diperlukan
            
        time.sleep(CHECK_INTERVAL)
