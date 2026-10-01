from flask import Flask, render_template, jsonify
import threading
import time

# Import worker dari file 2-Shot dan M&G
# Asumsi Anda punya file bot.py dan file baru mg_monitor.py
from bot import monitor_2shot_worker, get_2shot_data # Ganti dengan nama fungsi asli Anda
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
    return jsonify(get_status()) # Sesuaikan dengan nama fungsi di bot.py

if __name__ == '__main__':
    # Thread 2-Shot
    thread_2shot = threading.Thread(target=monitor_worker, daemon=True) # Sesuaikan
    thread_2shot.start()

    # Thread M&G
    thread_mg = threading.Thread(target=monitor_mg_worker, daemon=True)
    thread_mg.start()

    app.run(host='0.0.0.0', port=5000)
