from flask import Flask, jsonify
from flask_cors import CORS
import threading

# Import bot 2-Shot (sesuaikan nama file 2-Shot Anda, misal: twoshot_monitor.py)
from twoshot_monitor import monitor_worker as monitor_2shot_worker, get_2shot_data

# Import bot M&G
from mg_monitor import monitor_worker as monitor_mg_worker, get_mg_data

app = Flask(__name__)
CORS(app)

# Endpoint untuk 2-Shot (EX5B99)
@app.route('/api/status')
def get_status_2shot():
    return jsonify(get_2shot_data())

# Endpoint baru untuk M&G (EX24AE)
@app.route('/api/mg')
def get_status_mg():
    return jsonify(get_mg_data())

if __name__ == "__main__":
    # Jalankan bot 2-Shot di background
    threading.Thread(target=monitor_2shot_worker, daemon=True).start()
    
    # Jalankan bot M&G di background
    threading.Thread(target=monitor_mg_worker, daemon=True).start()
    
    app.run(host="0.0.0.0", port=5000)
