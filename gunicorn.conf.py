import os

# 強制即時 flush + 把 worker 輸出導到主控台
accesslog = "-"        # 訪問日誌 → 控制台
errorlog  = "-"        # 錯誤日誌 → 控制台
loglevel  = "info"
capture_output = True  # 捕獲 worker print

# 關鍵：綁定正確端口
bind = "0.0.0.0:8080"