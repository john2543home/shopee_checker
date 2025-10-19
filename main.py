import os, requests, time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DB_URL  = os.getenv('DB_URL')
BATCH   = int(os.getenv('BATCH', 20))
API_KEY = os.getenv('API_KEY')

# 加 retry + UA，免費實例休眠也不斷線
sess = requests.Session()
retries = Retry(total=3, backoff_factor=2, status_forcelist=[502,503,504])
sess.mount('https://', HTTPAdapter(max_retries=retries))
sess.headers.update({'User-Agent': 'RenderWorker/1.0'})

def update_status(row_id, status):
    sess.post(DB_URL, data={'id': row_id, 'status': status})

def job():
    while True:
        try:
            rows = sess.get(DB_URL, params={'limit': BATCH}, timeout=10).json()
        except Exception as e:
            print('fetch error:', e)
            time.sleep(30)
            continue

        if not rows:
            print('no work, sleep 5min')
            time.sleep(300)
            continue

        for r in rows:
            url = r['real_url']
            api = f'https://api.scrapingant.com/v2/general?url={url}&x-api-key={API_KEY}&wait_for_selector=.product-not-exist__text'
            try:
                html = sess.get(api, timeout=30).text
            except Exception as e:
                print('scrapingant error:', e)
                continue

            status = '失效' if 'product-not-exist__text' in html else '有效'
            update_status(r['id'], status)
            print(f"updated id={r['id']} -> {status}")

if __name__ == '__main__':
    job()