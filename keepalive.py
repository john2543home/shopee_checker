import main, time, threading
threading.Thread(target=main.job, daemon=True).start()
while True:
    time.sleep(86400)