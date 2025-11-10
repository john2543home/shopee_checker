import main
import logging

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)
log = logging.getLogger(__name__)

if __name__ == '__main__':
    log.info("🚀 蝦皮商品檢查器啟動 - 手動模式")
    log.info("⏰ 現在開始執行商品檢查...")
    
    # 只執行一次檢查
    try:
        main.job()
        log.info("✅ 商品檢查完成")
    except Exception as e:
        log.error("❌ 檢查失敗: %s", e)
    
    log.info("🏁 程式執行完畢，容器將停止")