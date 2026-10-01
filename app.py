from flask import Flask, render_template, jsonify
import threading
import os

# Import fungsi worker dan data dari bot.py (2-Shot) & mg_monitor.py (M&G)
from bot import monitor_2shot_worker, get_2shot_data
from mg_monitor import monitor_worker as monitor_mg_worker, get_mg_data

# 1. Inisialisasi Flask (harus ditaruh sebelum dekorator route)
app = Flask(__name__)

# --- BACKGROUND THREADS ---
# Dijalankan di luar `if __name__ == '__main__':` agar thread tetap berjalan saat di-deploy pakai Gunicorn
def start_background_threads():
    # Thread 2-Shot
    thread_2shot = threading.Thread(target=monitor_2shot_worker, daemon=True)
    thread_2shot.start()

    # Thread M&G
    thread_mg = threading.Thread(target=monitor_mg_worker, daemon=True)
    thread_mg.start()

# Jalankan thread pemantau saat file diimpor/dimuat
start_background_threads()


# --- ROUTING FLASK ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    """Endpoint status untuk 2-Shot"""
    return jsonify(get_2shot_data())

@app.route('/api/status_mg')
def api_status_mg():
    """Endpoint status untuk Meet & Greet"""
    return jsonify(get_mg_data())


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
