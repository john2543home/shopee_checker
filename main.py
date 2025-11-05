import os, time, requests, threading
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# === 檔案日誌：/tmp/worker.log ===
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('/tmp/worker.log'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

DB_URL  = os.getenv('DB_URL')  # 應該是 https://shopee-checker-i3ip.onrender.com/api/products
BATCH   = int(os.getenv('BATCH', 20))
API_KEY = os.getenv('API_KEY')

sess = requests.Session()
retries = Retry(total=3, backoff_factor=2, status_forcelist=[502, 503, 504])
sess.mount('https://', HTTPAdapter(max_retries=retries))

# 簡單的 API 請求頭部（適用於 Render API）
headers = {
    'User-Agent': 'ShopeeChecker/1.0',
    'Accept': 'application/json',
    'Accept-Encoding': 'identity'  # 明確要求不壓縮
}
sess.headers.update(headers)

def update_status(row_id, status):
    try:
        # 簡單的 POST 請求
        data = {'id': row_id, 'status': status}
        sess.post(DB_URL, data=data, timeout=30)
        log.info("Updated id=%s -> %s", row_id, status)
    except Exception as e:
        log.error("update_status failed: %s", e)

def job():
    log.info("worker started - DB_URL: %s", DB_URL)
    while True:
        for attempt in range(3):
            try:
                # 簡單的 GET 請求
                params = {'limit': BATCH}
                res = sess.get(DB_URL, params=params, timeout=30)
                
                # 記錄回應信息用於調試
                log.info("API Response - Status: %s, Length: %s", res.status_code, len(res.text))
                
                if res.status_code != 200:
                    log.warning("HTTP %s from API (attempt %s)", res.status_code, attempt+1)
                    time.sleep(5)
                    continue
                    
                if not res.text.strip():
                    log.warning("API returned empty body (attempt %s)", attempt+1)
                    time.sleep(5)
                    continue
                    
                try:
                    rows = res.json()
                    log.info("Successfully fetched %s items", len(rows))
                    break
                except Exception as e:
                    log.error("Invalid JSON from API (attempt %s): %s", attempt+1, e)
                    log.error("Response content: %.200s", res.text)
                    time.sleep(5)
                    continue
                    
            except Exception as e:
                log.warning("fetch attempt %s failed: %s", attempt+1, e)
                time.sleep(5)
        else:
            log.error("fetch failed 3 times, skip cycle")
            time.sleep(30)
            continue

        if not rows:
            log.info("no work, sleep 5min")
            time.sleep(300)
            continue

        for r in rows:
            url = r['real_url']
            api = f'https://api.scrapingant.com/v2/general?url={url}&x-api-key={API_KEY}&wait_for_selector=.product-not-exist__text'
            try:
                html = sess.get(api, timeout=30).text
            except Exception as e:
                log.error("scrapingant error: %s", e)
                continue

            status = '失效' if 'product-not-exist__text' in html else '有效'
            update_status(r['id'], status)
            log.info("updated id=%s -> %s", r['id'], status)

if __name__ == '__main__':
    job()