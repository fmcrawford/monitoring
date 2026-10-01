from flask import Flask, render_template, jsonify
import threading
import time

# Import worker dari file 2-Shot dan M&G
# Asumsi Anda punya file bot_2shot.py dan file baru mg_monitor.py
from bot_2shot import monitor_2shot_worker, get_2shot_data # Ganti dengan nama fungsi asli Anda
from mg_monitor import monitor_worker as monitor_mg_worker, get_mg_data

# ... (kode lainnya) ...

# Endpoint untuk 2-Shot
@app.route('/api/status')
def api_status():
    return jsonify(get_2shot_data())

# Endpoint Baru untuk M&G
@app.route('/api/status_mg')
def api_status_mg():
    return jsonify(get_mg_data())
app = Flask(__name__)

# --- ROUTING FLASK ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    # Mengambil data dari variabel global bot 2-shot Anda
    return jsonify(get_2shot_data())

# --- RUNNING BACKGROUND THREADS & SERVER ---
if __name__ == '__main__':
    # 1. Jalankan Bot 2-Shot di background
    thread_2shot = threading.Thread(target=monitor_2shot_worker, daemon=True)
    thread_2shot.start()

    # 2. Jalankan Bot M&G di background
    thread_mg = threading.Thread(target=monitor_mg_worker, daemon=True)
    thread_mg.start()

    print("Memulai Web Server dan Bot Monitor...")
    # Jalankan Flask Server. Gunakan host 0.0.0.0 agar bisa diakses eksternal saat di-deploy
    app.run(host='0.0.0.0', port=5000)
