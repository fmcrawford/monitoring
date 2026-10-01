import time
import threading
import requests
from datetime import datetime
from curl_cffi import requests as cffi_requests
from flask import Flask, jsonify
from flask_cors import CORS

# ==========================================
# KONFIGURASI GLOBAL
# ==========================================
WEBHOOK_URL = "https://discord.com/api/webhooks/1552512118736035971/ezzci7fFs33b-G8RTO1m8vJr9vgCECtxAVFXemVGQAOEn6gj_WY8PldhlHQJd63OFAqC"
API_URL = "https://jkt48.com/api/v1/exclusives/EX24AE/bonus?lang=id"
CHECK_INTERVAL = 60  # Cek API setiap 60 detik (1 menit)

# Daftar Pantauan Khusus
TARGET_MEMBERS = [
    "Grace Octaviani", 
    "Michelle Alexandra", 
    "Jazzlyn Trisha", 
    "Fiony Alveria", 
    "Indah Cahya", 
    "Marsha Lenathea", 
    "Nina Tutachia"
]

# Variabel Global Status untuk UI Web & Endpoint Flask
LATEST_STATUS_MG = {
    "last_check": 0,
    "total_quota": 0,
    "members": []
}

# State Tracker Notifikasi Discord
state = {
    "last_sunday_check_date": None,
    "last_monday_update_date": None,
    "last_daily_summary_date": None,
    "initial_sent": False  
}

# ==========================================
# FUNGSI EXPORT UNTUK FLASK / APP.PY
# ==========================================
def get_mg_data():
    """Mengembalikan data M&G terbaru untuk endpoint Flask / UI."""
    return LATEST_STATUS_MG

# ==========================================
# FUNGSI PEMROSESAN DATA API
# ==========================================
def fetch_jkt48_api():
    """Mengambil data dari API JKT48 dengan bypass WAF."""
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://jkt48.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = cffi_requests.get(
            API_URL, 
            impersonate="chrome120", 
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✅ Berhasil fetch data API!")
            return response.json()
        else:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ❌ Gagal fetch API, Status: {response.status_code}")
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ❌ Error koneksi API: {e}")
        
    return None

def update_web_status_mg(api_data):
    """Memformat raw data API M&G agar strukturnya siap digunakan oleh UI Web."""
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
    """Agregasi total kuota tiket serta mencatat detail sesi & jalur yang masih tersedia."""
    member_status = {}
    
    if not api_data or "data" not in api_data:
        return member_status

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
            
    sorted_members = dict(sorted(member_status.items(), key=lambda item: item[1]["total_quota"], reverse=True))
    return sorted_members

# ==========================================
# FUNGSI HELPER DISCORD NOTIFICATION
# ==========================================
def send_discord_notification(title, description, color, fields=None):
    """Fungsi helper untuk kirim embed ke Discord."""
    embed = {
        "title": title,
        "description": description,
        "color": color,
        "timestamp": datetime.utcnow().isoformat()
    }
    if fields:
        embed["fields"] = fields

    payload = {"embeds": [embed]}
    try:
        res = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        if res.status_code in [200, 204]:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 Webhook Discord berhasil terkirim!")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Gagal kirim Webhook, Status: {res.status_code}")
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error webhook: {e}")

def get_target_member_details(member_status):
    """Format teks detail sisa tiket beserta sesi dan jalur untuk member pantauan."""
    target_details = []
    for name in TARGET_MEMBERS:
        if name in member_status:
            quota = member_status[name]['total_quota']
            if quota == 0:
                status_text = "🔥 **Sold Out** *(Berhak Tambahan Sesi)*"
            else:
                sessions_left = "\n   ↳ ".join(member_status[name]['available_sessions'])
                status_text = f"🎟️ Sisa **{quota}** tiket\n   ↳ {sessions_left}"
            target_details.append(f"• **{name}**: {status_text}")
    return "\n".join(target_details) if target_details else "Tidak ada data."

def get_eligible_members_list(member_status):
    """Mendapatkan daftar member yang sold out (berhak mendapat sesi tambahan)."""
    eligible = [name for name, data in member_status.items() if data['total_quota'] == 0]
    if not eligible:
        return "Belum ada member yang Sold Out."
    eligible.sort()
    return ", ".join(eligible)

def build_standard_fields(member_status):
    """Membangun field standar (Total Status, Pantauan Khusus, Kandidat Tambahan)."""
    sold_out_count = sum(1 for data in member_status.values() if data['total_quota'] == 0)
    available_count = sum(1 for data in member_status.values() if data['total_quota'] > 0)

    return [
        {
            "name": "📊 Status Keseluruhan",
            "value": f"Member Tiket Tersedia: **{available_count}**\nMember Sold Out: **{sold_out_count}**",
            "inline": False
        },
        {
            "name": "🎯 Pantauan Khusus (Sesi & Jalur)",
            "value": get_target_member_details(member_status),
            "inline": False
        },
        {
            "name": "🌟 Kandidat Tambahan Sesi (Sold Out)",
            "value": get_eligible_members_list(member_status),
            "inline": False
        }
    ]

# ==========================================
# TRIGGER LOGIC NOTIFIKASI DISCORD
# ==========================================
def send_startup_summary(member_status):
    """Mengirim ringkasan awal saat skrip baru dijalankan."""
    send_discord_notification(
        title="🟢 Monitoring M&G Aktif!",
        description="Skrip berhasil terhubung ke API JKT48.",
        color=3066993, # Hijau
        fields=build_standard_fields(member_status)
    )

def check_sunday_extra_session(member_status, now):
    """Notifikasi Alert Hari Minggu jam 12:00 untuk sesi tambahan."""
    current_date = now.strftime("%Y-%m-%d")
    if state["last_sunday_check_date"] == current_date:
        return

    eligible_members = [name for name, data in member_status.items() if data["total_quota"] == 0]

    if eligible_members:
        eligible_members.sort()
        desc = "**Member yang telah memenuhi syarat (Sold Out semua sesi) minggu ini:**\n\n"
        desc += "\n".join([f"⭐ **{name}**" for name in eligible_members])
        send_discord_notification(
            title="🎯 FINAL: Kualifikasi Tambahan Sesi M&G",
            description=desc,
            color=16711680 # Merah
        )
    else:
        send_discord_notification(
            title="🎯 FINAL: Evaluasi Tambahan Sesi",
            description="Belum ada member yang *Sold Out* di semua sesinya minggu ini.",
            color=8421504 # Abu-abu
        )
    
    state["last_sunday_check_date"] = current_date

def handle_monday_api_update(member_status, now):
    """Logic update hari Senin jam 19:00: Notifikasi sesi baru."""
    current_date = now.strftime("%Y-%m-%d")
    if state["last_monday_update_date"] == current_date:
        return

    send_discord_notification(
        title="🔄 UPDATE SESI BARU M&G (Senin 19:00)",
        description="API telah memunculkan ketersediaan jadwal/sesi baru!\nBerikut update ketersediaannya:",
        color=16766720, # Kuning/Oranye
        fields=build_standard_fields(member_status)
    )
    state["last_monday_update_date"] = current_date

def send_daily_summary(member_status, now):
    """Mengirim rangkuman sisa tiket tiap jam 08:00 pagi."""
    current_date = now.strftime("%Y-%m-%d")
    if state["last_daily_summary_date"] == current_date:
        return

    send_discord_notification(
        title="📊 Daily Summary Tiket M&G",
        description="Rangkuman status tiket harian.",
        color=3447003, # Biru
        fields=build_standard_fields(member_status)
    )
    state["last_daily_summary_date"] = current_date

# ==========================================
# WORKER UTAMA (LOOP MONITORING)
# ==========================================
def monitor_worker():
    """Fungsi utama monitoring yang dipanggil oleh app.py."""
    print("Mulai memonitor API JKT48...")
    while True:
        now = datetime.now()
        api_data = fetch_jkt48_api()
        
        if api_data:
            # Update data internal untuk Flask UI Web
            update_web_status_mg(api_data)
            
            # Olah data untuk Discord Bot
            member_status = process_member_quotas(api_data)
            
            # Kirim notifikasi pertama kali saat skrip dinyalakan
            if not state["initial_sent"]:
                send_startup_summary(member_status)
                state["initial_sent"] = True

            # 1. Cek Syarat Tambahan Sesi: Tiap Minggu, Jam 12:00 ke atas
            if now.weekday() == 6 and now.hour >= 12:
                check_sunday_extra_session(member_status, now)
                
            # 2. Cek Update Penambahan Sesi Baru: Tiap Senin, Jam 19:00 ke atas
            if now.weekday() == 0 and now.hour >= 19:
                handle_monday_api_update(member_status, now)
                
            # 3. Daily summary tiap jam 08:00
            if now.hour == 8:
                send_daily_summary(member_status, now)

        time.sleep(CHECK_INTERVAL)

# ==========================================
# STANDALONE RUNNER (OPSIONAL)
# ==========================================
if __name__ == '__main__':
    app = Flask(__name__)
    CORS(app)

    @app.route('/api/status')
    def get_status():
        return jsonify(LATEST_STATUS_MG)

    # Jalankan thread pemantau M&G jika file dijalankan secara langsung
    t = threading.Thread(target=monitor_worker, daemon=True)
    t.start()

def get_2shot_data():
    return LATEST_STATUS_2SHOT  # Sesuaikan nama variabel global status 2-Shot Anda
    
    app.run(host='0.0.0.0', port=5002)
