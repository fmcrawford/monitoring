import os
import threading
from flask import Flask
from bot import main_loop

app = Flask(__name__)

# Jalankan bot di background thread secara otomatis saat app di-load
bot_thread = threading.Thread(target=main_loop, daemon=True)
bot_thread.start()

@app.route('/')
def home():
    return "JKT48 Bot Monitoring is Active and Running!", 200
