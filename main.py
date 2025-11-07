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

DB_URL  = os.getenv('DB_URL')
BATCH   = int(os.getenv('BATCH', 20))
API_KEY = os.getenv('API_KEY')

sess = requests.Session()
retries = Retry(total=3, backoff_factor=2, status_forcelist=[502, 503, 504])
sess.mount('https://', HTTPAdapter(max_retries=retries))

headers = {
    'User-Agent': 'ShopeeChecker/1.0',
    'Accept': 'application/json',
    'Accept-Encoding': 'identity'
}
sess.headers.update(headers)

def update_status(row_id, status):
    """只更新失效的商品狀態"""
    try:
        if status == '失效':
            data = {'id': row_id, 'status': status}
            sess.post(DB_URL, data=data, timeout=30)
            log.info("✅ Recorded removed product: id=%s", row_id)
    except Exception as e:
        log.error("update_status failed: %s", e)

def job():
    log.info("worker started - DB_URL: %s", DB_URL)
    
    # 單次執行，移除 while True 循環
    for attempt in range(3):
        try:
            params = {'limit': BATCH}
            res = sess.get(DB_URL, params=params, timeout=30)
            
            if res.status_code != 200:
                log.warning("HTTP %s from API (attempt %s)", res.status_code, attempt+1)
                time.sleep(5)
                continue
                
            try:
                rows = res.json()
                log.info("🔍 Checking %s products", len(rows))
                break
            except Exception as e:
                log.error("Invalid JSON from API (attempt %s): %s", attempt+1, e)
                time.sleep(5)
                continue
                
        except Exception as e:
            log.warning("fetch attempt %s failed: %s", attempt+1, e)
            time.sleep(5)
    else:
        log.error("fetch failed 3 times, skip cycle")
        return

    if not rows:
        log.info("📭 No products to check")
        return

    for r in rows:
        url = r['real_url']
        log.info("🔎 Checking product: %s", url)
        
        api = f'https://api.scrapingant.com/v2/general?url={url}&x-api-key={API_KEY}&browser=true'
        try:
            response = sess.get(api, timeout=60)
            html = response.text
            
            # 精確的下架檢測 - 使用找到的確切標誌
            if 'product-not-exist__text' in html:
                status = '失效'
                log.warning("🚫 Product REMOVED: %s", url)
            else:
                status = '有效'
                log.info("✅ Product ACTIVE: %s", url)
            
            update_status(r['id'], status)
            
        except Exception as e:
            log.error("scrapingant error for %s: %s", url, e)
            continue

    log.info("✅ Single batch completed - exiting")

if __name__ == '__main__':
    job()