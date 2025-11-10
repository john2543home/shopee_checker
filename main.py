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

sess = requests.Session()
retries = Retry(total=3, backoff_factor=2, status_forcelist=[502, 503, 504])
sess.mount('https://', HTTPAdapter(max_retries=retries))

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
    """精確的下架檢測 - 針對蝦皮下架頁面"""
    # 記錄部分HTML用於除錯（前500字符）
    html_preview = html[:500] if len(html) > 500 else html
    log.info("📄 HTML preview: %s", html_preview)
    
    # 確切的下架標誌 - 基於實際下架頁面分析
    exact_removed_indicators = [
        'product-not-exist__text">此商品不存在</div>',  # 完整HTML標籤
        'product-not-exist__text',                      # CSS類名
        '此商品不存在',                                  # 文字內容
        '商品已下架',
        '很抱歉，您訪問的頁面不存在',
        '該商品已不存在'
    ]
    
    for indicator in exact_removed_indicators:
        if indicator in html:
            log.info("🎯 確切檢測到下架標誌: %s", indicator)
            return True
    
    # 檢查正常商品頁面的特徵
    active_product_indicators = [
        'shopee-product-info',
        'product-detail',
        'item-review',
        'product-briefing',
        'add-to-cart',
        '加入購物車',
        '商品規格',
        '商品評價'
    ]
    
    for indicator in active_product_indicators:
        if indicator in html:
            log.info("🏪 檢測到正常商品頁面特徵: %s", indicator)
            return False
    
    # 謹慎使用模糊標誌
    weak_removed_indicators = [
        '404',
        'out of stock',
        'sold out'
    ]
    
    weak_match_count = 0
    for indicator in weak_removed_indicators:
        if indicator.lower() in html.lower():
            weak_match_count += 1
            log.info("⚠️ 檢測到模糊下架標誌: %s", indicator)
    
    # 只有在沒有檢測到正常頁面特徵時，才考慮模糊標誌
    if weak_match_count >= 2:
        log.info("🎯 多個模糊標誌確認商品下架")
        return True
    
    # 預設情況：沒有明確證據就認為商品有效
    log.info("🔍 未檢測到明確下架證據，商品判定為有效")
    return False

def job():
    log.info("worker started - DB_URL: %s", DB_URL)
    
    # 單次執行
    for attempt in range(3):
        try:
            params = {'limit': BATCH}
            log.info("🔍 嘗試從 API 獲取商品 (attempt %s)", attempt+1)
            
            # 禁用壓縮，確保能正確解析 JSON
            api_headers = {
                'User-Agent': 'ShopeeChecker/1.0',
                'Accept': 'application/json',
                'Accept-Encoding': 'identity'  # 禁用壓縮
            }
            
            res = sess.get(DB_URL, params=params, timeout=30, headers=api_headers)
            
            # 添加詳細除錯信息
            log.info("🔍 API 回應狀態碼: %s", res.status_code)
            log.info("🔍 API 回應標頭: %s", dict(res.headers))
            
            if res.status_code != 200:
                log.warning("HTTP %s from API (attempt %s)", res.status_code, attempt+1)
                time.sleep(5)
                continue
                
            try:
                rows = res.json()
                log.info("✅ 成功解析 JSON，找到 %s 個商品", len(rows))
                break
            except Exception as e:
                log.error("❌ JSON 解析失敗 (attempt %s): %s", attempt+1, e)
                log.error("❌ 回應內容開始: %s", res.text[:200])
                time.sleep(5)
                continue
                
        except Exception as e:
            log.warning("fetch attempt %s failed: %s", attempt+1, e)
            time.sleep(5)
    else:
        log.error("🚫 獲取商品失敗 3 次，跳過本輪檢查")
        return

    if not rows:
        log.info("📭 No products to check")
        return

    removed_count = 0
    active_count = 0
    
    for r in rows:
        url = r['real_url']
        log.info("🔎 Checking product: %s", url)
        
        try:
            # 免費方案：直接訪問蝦皮
            shopee_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br'
            }
            
            response = sess.get(url, headers=shopee_headers, timeout=30)
            log.info("🔍 蝦皮頁面狀態碼: %s", response.status_code)
            
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
            log.error("❌ 訪問商品頁面失敗: %s", e)
            continue

    log.info("📊 Check completed: %s active, %s removed", active_count, removed_count)
    log.info("✅ Single batch completed - exiting")

if __name__ == '__main__':
    job()