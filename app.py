from flask import Flask
import threading, main

app = Flask(__name__)

# 背景執行你的輪詢
threading.Thread(target=main.job, daemon=True).start()

@app.route("/")
def ok():
    return "OK", 200