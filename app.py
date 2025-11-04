from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)
DATABASE = 'products.db'

def init_db():
    """初始化資料庫"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY, real_url TEXT, status TEXT)''')
    
    # 插入示例數據（如果表是空的）
    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] == 0:
        sample_products = [
            (1, 'https://shopee.tw/product1', '有效'),
            (2, 'https://shopee.tw/product2', '有效'),
            # 添加你的真實商品連結
        ]
        c.executemany('INSERT INTO products VALUES (?, ?, ?)', sample_products)
        print("Added sample products to database")
    
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/products', methods=['GET'])
def get_products():
    """Fly.io worker 從這裡獲取待檢查的商品"""
    limit = request.args.get('limit', 10, type=int)
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''SELECT id, real_url FROM products 
                 WHERE status IS NULL OR status != "失效" 
                 LIMIT ?''', (limit,))
    rows = c.fetchall()
    conn.close()
    
    products = [dict(row) for row in rows]
    print(f"Returning {len(products)} products to worker")
    return jsonify(products)

@app.route('/api/products', methods=['POST'])
def update_product():
    """Fly.io worker 在這裡更新商品狀態"""
    product_id = request.form.get('id', type=int)
    status = request.form.get('status')
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('UPDATE products SET status = ? WHERE id = ?', (status, product_id))
    conn.commit()
    conn.close()
    
    print(f"Updated product {product_id} to {status}")
    return jsonify({'success': True})

@app.route("/")
def home():
    return "Product API Server is Running"

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=10000)