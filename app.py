from flask import Flask, jsonify, render_template
from flask_cors import CORS
import threading

# Import dari bot.py (untuk 2-Shot)
from bot import monitor_worker as monitor_2shot_worker, get_2shot_data

# Import dari mg_monitor.py (untuk Meet & Greet)
from mg_monitor import monitor_worker as monitor_mg_worker, get_mg_data

app = Flask(__name__)
CORS(app)

# =================================================================
# JALANKAN BACKGROUND THREAD DI SINI AGAR TERBACA OLEH GUNICORN
# =================================================================
t_2shot = threading.Thread(target=monitor_2shot_worker, daemon=True)
t_2shot.start()

t_mg = threading.Thread(target=monitor_mg_worker, daemon=True)
t_mg.start()
# =================================================================

@app.route('/')
def index():
    return render_template('index.html')

# Endpoint API 2-Shot
@app.route('/api/status')
def api_2shot():
    return jsonify(get_2shot_data())

# Endpoint API Meet & Greet
@app.route('/api/mg')
def api_mg():
    return jsonify(get_mg_data())

if __name__ == '__main__':
    # Blok ini hanya akan berjalan jika Anda tes lokal dengan 'python app.py'
    app.run(host='0.0.0.0', port=5000)
