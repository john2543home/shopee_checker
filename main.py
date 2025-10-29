import os, time, requests, threading, json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# === 檔案日誌：/tmp/worker.log ===
import logging, os
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

# 創建更穩定的 session
sess = requests.Session()
retries = Retry(total=3, backoff_factor=2, status_forcelist=[502, 503, 504, 429])
sess.mount('https://', HTTPAdapter(max_retries=retries))
sess.mount('http://', HTTPAdapter(max_retries=retries))

# 完整的瀏覽器頭部
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br'
}
sess.headers.update(headers)

def update_status(row_id, status):
    """更新商品狀態到資料庫"""
    try:
        response = sess.post(DB_URL, data={'id': row_id, 'status': status}, timeout=30)
        if response.status_code != 200:
            log.error("Update status failed for id=%s, status=%s, code=%s", row_id, status, response.status_code)
    except Exception as e:
        log.error("Update status error for id=%s: %s", row_id, e)

def fetch_rows():
    """從資料庫獲取待處理的商品列表"""
    for attempt in range(3):
        try:
            response = sess.get(DB_URL, params={'limit': BATCH}, timeout=30)
            
            # 檢查回應內容類型
            content_type = response.headers.get('content-type', '')
            if 'application/json' in content_type:
                rows = response.json()
                return rows
            else:
                # 如果不是 JSON，嘗試解析
                log.warning("Response is not JSON, attempting to parse: %s", response.text[:100])
                rows = json.loads(response.text)
                return rows
                
        except json.JSONDecodeError as e:
            log.warning("JSON decode attempt %s failed: %s", attempt+1, e)
            log.warning("Response content: %s", response.text[:200] if 'response' in locals() else 'No response')
            time.sleep(5)
        except Exception as e:
            log.warning("Fetch attempt %s failed: %s", attempt+1, e)
            time.sleep(5)
    
    return None

def check_product_status(url):
    """使用 ScrapingAnt 檢查商品狀態"""
    api_url = f'https://api.scrapingant.com/v2/general?url={url}&x-api-key={API_KEY}&wait_for_selector=.product-not-exist__text'
    
    try:
        response = sess.get(api_url, timeout=60)  # 增加超時時間
        
        if response.status_code != 200:
            log.error("ScrapingAnt API error: HTTP %s", response.status_code)
            return '未知'
        
        html = response.text
        
        # 檢查商品是否存在
        if 'product-not-exist__text' in html:
            return '失效'
        else:
            return '有效'
            
    except Exception as e:
        log.error("ScrapingAnt error for %s: %s", url, e)
        return '未知'

def job():
    log.info("Worker started with DB_URL: %s", DB_URL)
    
    while True:
        try:
            # 獲取待處理的商品
            rows = fetch_rows()
            
            if rows is None:
                log.error("Failed to fetch rows after 3 attempts, skip cycle")
                time.sleep(60)
                continue
                
            if not rows:
                log.info("No work available, sleep 5 minutes")
                time.sleep(300)
                continue

            log.info("Processing %s products", len(rows))
            
            # 處理每個商品
            for row in rows:
                if 'id' not in row or 'real_url' not in row:
                    log.warning("Invalid row data: %s", row)
                    continue
                
                url = row['real_url']
                log.info("Checking product: %s", url)
                
                # 檢查商品狀態
                status = check_product_status(url)
                
                # 更新狀態
                update_status(row['id'], status)
                log.info("Updated id=%s -> %s", row['id'], status)
                
                # 避免請求過於頻繁
                time.sleep(2)
                
        except Exception as e:
            log.error("Unexpected error in main loop: %s", e)
            time.sleep(30)

if __name__ == '__main__':
    job()