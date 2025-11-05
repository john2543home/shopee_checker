from flask import Flask, request, jsonify
import threading, time, os, sys

app = Flask(__name__)

# 判斷運行環境
IS_FLY_IO = os.getenv('FLY_APP_NAME')
IS_RENDER = os.getenv('RENDER')

print(f"🔍 Environment detection: FLY_APP_NAME={IS_FLY_IO}, RENDER={IS_RENDER}")

if IS_FLY_IO:
    # ===== FLY.IO WORKER 模式 =====
    print("🚀 Starting in Fly.io Worker mode")
    
    def start_worker():
        time.sleep(5)
        print("🔄 Importing main module...")
        import main
        print("✅ Starting job...")
        main.job()
    
    threading.Thread(target=start_worker, daemon=True).start()
    
    @app.route("/")
    def health_check():
        return "Fly.io Worker Running", 200

else:
    # ===== RENDER API 模式 =====
    print("🌐 Starting in API Server mode")
    
    # 所有商品初始狀態為空（或者你可以設置為"有效"）
    # 只有當商品下架時才會被標記為"失效"
    products = [
        {"id": 1, "real_url": "https://s.shopee.tw/AKPCVLTJJI", "status": None},
        {"id": 2, "real_url": "https://s.shopee.tw/3VYfxgIky9", "status": None},
        {"id": 3, "real_url": "https://s.shopee.tw/9zm9iEA070", "status": None},
        # 添加更多商品，status 設為 None
    ]

    @app.route('/api/products', methods=['GET'])
    def get_products():
        """返回需要檢查的商品（status 不是 '失效' 的）"""
        try:
            limit = request.args.get('limit', 10, type=int)
            # 只返回尚未被標記為失效的商品
            pending_products = [p for p in products if p.get('status') != '失效'][:limit]
            print(f"✅ Returning {len(pending_products)} products to check")
            return jsonify(pending_products)
        except Exception as e:
            print(f"❌ Error in get_products: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/products', methods=['POST'])
    def update_product():
        """只更新失效的商品狀態"""
        try:
            product_id = request.form.get('id', type=int)
            status = request.form.get('status')
            
            # 只處理失效的商品
            if status == '失效':
                for product in products:
                    if product['id'] == product_id:
                        product['status'] = status
                        print(f"🚫 Recorded removed product: id={product_id}, url={product['real_url']}")
                        return jsonify({'success': True, 'message': 'Removed product recorded'})
            
            return jsonify({'success': True, 'message': 'No update needed'})
            
        except Exception as e:
            print(f"❌ Error in update_product: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/removed-products", methods=['GET'])
    def get_removed_products():
        """專門查看已下架的商品"""
        removed_products = [p for p in products if p.get('status') == '失效']
        return jsonify({
            'count': len(removed_products),
            'removed_products': removed_products
        })

    @app.route("/")
    def home():
        return "✅ Product API Server is Running - Only tracks removed products"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)