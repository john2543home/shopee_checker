import os, time, requests, threading
import urllib.parse
import html as html_parser
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

def check_removed(html):
    """檢測商品是否下架 - 只檢測確切標誌"""
    # 記錄部分HTML用於除錯
    html_sample = html[:200] if len(html) > 200 else html
    log.debug("HTML sample: %s", html_sample)
    
    # 方法1: 直接檢測確切標誌
    if '此商品不存在' in html:
        log.info("🎯 Detected '此商品不存在' in raw HTML")
        return True
        
    # 方法2: URL解碼後檢測
    try:
        decoded_html = urllib.parse.unquote(html)
        if '此商品不存在' in decoded_html:
            log.info("🎯 Detected '此商品不存在' in URL decoded HTML")
            return True
    except Exception as e:
        log.debug("URL decode failed: %s", e)
        
    # 方法3: HTML實體解碼後檢測
    try:
        decoded_html = html_parser.unescape(html)
        if '此商品不存在' in decoded_html:
            log.info("🎯 Detected '此商品不存在' in HTML entity decoded HTML")
            return True
    except Exception as e:
        log.debug("HTML entity decode failed: %s", e)
    
    # 只檢測確切的蝦皮下架標誌，移除模糊的錯誤標誌
    # 這樣可以避免誤判正常商品
    
    return False

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

    removed_count = 0
    active_count = 0
    
    for r in rows:
        url = r['real_url']
        log.info("🔎 Checking product: %s", url)
        
        # 增加 browser_wait=8000 讓蝦皮JS有足夠時間執行
        api = f'https://api.scrapingant.com/v2/general?url={url}&x-api-key={API_KEY}&browser=true&browser_wait=8000'
        
        try:
            response = sess.get(api, timeout=90)  # 增加超時時間
            html = response.text
            
            # 使用精確的下架檢測
            if check_removed(html):
                status = '失效'
                removed_count += 1
                log.warning("🚫 Product REMOVED: %s", url)
            else:
                status = '有效'
                active_count += 1
                log.info("✅ Product ACTIVE: %s", url)
            
            update_status(r['id'], status)
            
        except Exception as e:
            log.error("scrapingant error for %s: %s", url, e)
            continue

    log.info("📊 Check completed: %s active, %s removed", active_count, removed_count)
    log.info("✅ Single batch completed - exiting")

if __name__ == '__main__':
    job()