from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# 簡單的記憶體資料庫（避免 SQLite 問題）
products = [
    {"id": 1, "real_url": "https://shopee.tw/product1", "status": "有效"},
    {"id": 2, "real_url": "https://shopee.tw/product2", "status": "有效"},
    {"id": 3, "real_url": "https://shopee.tw/product3", "status": "有效"},
]

@app.route('/api/products', methods=['GET'])
def get_products():
    """Fly.io worker 從這裡獲取待檢查的商品"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        # 返回需要檢查的商品（status 不是 '失效' 的）
        pending_products = [p for p in products if p.get('status') != '失效'][:limit]
        
        print(f"✅ Returning {len(pending_products)} products")
        return jsonify(pending_products)
        
    except Exception as e:
        print(f"❌ Error in get_products: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/products', methods=['POST'])
def update_product():
    """Fly.io worker 在這裡更新商品狀態"""
    try:
        product_id = request.form.get('id', type=int)
        status = request.form.get('status')
        
        # 更新商品狀態
        for product in products:
            if product['id'] == product_id:
                product['status'] = status
                print(f"✅ Updated product {product_id} to {status}")
                return jsonify({'success': True})
        
        print(f"❌ Product {product_id} not found")
        return jsonify({'error': 'Product not found'}), 404
        
    except Exception as e:
        print(f"❌ Error in update_product: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/")
def home():
    return "✅ Product API Server is Running"

@app.route("/api/products", methods=['OPTIONS'])
def options_products():
    """處理 CORS 預檢請求"""
    return '', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)