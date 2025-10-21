# app.py
from flask import Flask
import threading, main, time, os

# 強制即時 flush
os.environ["PYTHONUNBUFFERED"] = "1"

app = Flask(__name__)

@app.route("/")
def ok():
    return "OK", 200

# 背景輪詢
threading.Thread(target=main.job, daemon=True).start()