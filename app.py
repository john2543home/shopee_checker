from flask import Flask
import threading, time, os, sys

# 強制即時 flush
os.environ["PYTHONUNBUFFERED"] = "1"
sys.stdout.flush()

app = Flask(__name__)

def start_worker():
    time.sleep(5)          # 等 gunicorn 完全起來
    import main            # 這時才載入，保證在 worker 內
    main.job()

@app.route("/")
def ok():
    return "OK", 200

# 在 worker 啟動後才開 thread
threading.Thread(target=start_worker, daemon=True).start()