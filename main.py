import os, requests, time

DB_URL   = os.getenv('DB_URL')
BATCH    = int(os.getenv('BATCH', 10))
API_KEY  = os.getenv('API_KEY', 'YOUR_SCRAPINGANT_KEY')   # 免費 1000 次/月

def update_status(row_id, status):
    requests.post(DB_URL, data={'id': row_id, 'status': status})

def job():
    while True:
        rows = requests.get(DB_URL, params={'limit': BATCH}).json()
        if not rows:
            time.sleep(300)
            continue
        for r in rows:
            url  = r['real_url']
            api  = f'https://api.scrapingant.com/v2/general?url={url}&x-api-key={API_KEY}&wait_for_selector=.product-not-exist__text'
            html = requests.get(api, timeout=30).text
            status = '失效' if 'product-not-exist__text' in html else '有效'
            update_status(r['id'], status)

if __name__ == '__main__':
    job()