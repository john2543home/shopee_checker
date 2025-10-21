import os, time, requests, threading
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

sess = requests.Session()
retries = Retry(total=3, backoff_factor=2, status_forcelist=[502, 503, 504])
sess.mount('https://', HTTPAdapter(max_retries=retries))
sess.headers.update({'User-Agent': 'RenderWorker/1.0'})

def update_status(row_id, status):
    sess.post(DB_URL, data={'id': row_id, 'status': status})

def job():
    log.info("worker started")
    while True:
        try:
            rows = sess.get(DB_URL, params={'limit': BATCH}, timeout=10).json()
        except Exception as e:
            log.error("fetch error: %s", e)
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