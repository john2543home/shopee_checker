import os, requests, json, time
from playwright.sync_api import sync_playwright

DB_URL = os.getenv('DB_URL')          # Render 環境變數
CHECK_BATCH = int(os.getenv('BATCH', 10))

def update_status(row_id, status):
    # 回寫你的 InfinityFree MySQL
    requests.post(DB_URL, data={'id': row_id, 'status': status})

def job():
    while True:
        # 1. 去 InfinityFree 撈「未知」連結
        rows = requests.get(DB_URL, params={'limit': CHECK_BATCH}).json()
        if not rows:
            time.sleep(300)           # 5 分鐘後再撈
            continue

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
            page = browser.new_page(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            for r in rows:
                page.goto(r['real_url'], wait_until='domcontentloaded', timeout=15000)
                if page.locator('.product-not-exist__text').count():
                    update_status(r['id'], '失效')
                else:
                    update_status(r['id'], '有效')
            browser.close()

if __name__ == '__main__':
    job()