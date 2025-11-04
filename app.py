from flask import Flask, request, jsonify
import threading, time, os, sys

app = Flask(__name__)

# 判斷運行環境
IS_FLY_IO = os.getenv('FLY_APP_NAME')  # Fly.io 會設置這個
IS_RENDER = os.getenv('RENDER')        # Render 會設置這個

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

    @app.route("/health")
    def health():
        return "OK", 200

else:
    # ===== RENDER API 模式 (或本地開發) =====
    print("🌐 Starting in API Server mode")
    
    products = [
        {"id": 1, "real_url": "https://shopee.tw/product1", "status": "有效"},
        {"id": 2, "real_url": "https://shopee.tw/product2", "status": "有效"},
        {"id": 3, "real_url": "https://shopee.tw/product3", "status": "有效"},
    ]

    @app.route('/api/products', methods=['GET'])
    def get_products():
        try:
            limit = request.args.get('limit', 10, type=int)
            pending_products = [p for p in products if p.get('status') != '失效'][:limit]
            print(f"✅ Returning {len(pending_products)} products")
            return jsonify(pending_products)
        except Exception as e:
            print(f"❌ Error in get_products: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/products', methods=['POST'])
    def update_product():
        try:
            product_id = request.form.get('id', type=int)
            status = request.form.get('status')
            for product in products:
                if product['id'] == product_id:
                    product['status'] = status
                    print(f"✅ Updated product {product_id} to {status}")
                    return jsonify({'success': True})
            return jsonify({'error': 'Product not found'}), 404
        except Exception as e:
            print(f"❌ Error in update_product: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/")
    def home():
        return "✅ Product API Server is Running"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)