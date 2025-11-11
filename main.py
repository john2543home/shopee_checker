from playwright.sync_api import sync_playwright
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
log = logging.getLogger(__name__)

def check_shopee_product(url):
    """使用 Playwright 檢測蝦皮商品狀態"""
    log.info(f"🔍 開始檢查: {url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # 訪問商品頁面
            page.goto(url, timeout=30000)
            page.wait_for_timeout(5000)  # 等待頁面加載
            
            # 檢查下架元素
            removed_element = page.query_selector('div.product-not-exist__text')
            if removed_element:
                log.info("🎯 檢測到商品已下架")
                return "失效"
            else:
                log.info("✅ 商品正常上架")
                return "有效"
                
        except Exception as e:
            log.error(f"❌ 檢查失敗: {e}")
            return "錯誤"
        finally:
            browser.close()

def main():
    log.info("🛍️ 蝦皮商品檢查器啟動")
    
    # 測試商品列表
    test_products = [
        "https://s.shopee.tw/AKPCVLTJJI",
        "https://s.shopee.tw/3VYfxgIky9", 
        "https://s.shopee.tw/9zm9iEA070"
    ]
    
    for url in test_products:
        status = check_shopee_product(url)
        log.info(f"📊 結果: {url} -> {status}")

if __name__ == '__main__':
    main()