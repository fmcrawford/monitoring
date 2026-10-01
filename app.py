import os
import threading
from flask import Flask, jsonify, render_template
from bot import main_loop, LATEST_STATUS

app = Flask(__name__)

# Jalankan bot di background thread
bot_thread = threading.Thread(target=main_loop, daemon=True)
bot_thread.start()

# Menampilkan Halaman Dashboard UI
@app.route('/')
def home():
    return render_template('index.html')

# Endpoint API yang diambil oleh UI Web secara real-time
@app.route('/api/status')
def api_status():
    return jsonify(LATEST_STATUS)
