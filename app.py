from flask import Flask, request, render_template, redirect, url_for, session, flash, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import mysql.connector
import logging
import re
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import uuid

# Setting
logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__, static_folder='static')
app.secret_key = 'your_secret_key'  # Replace with a real secret key
socketio = SocketIO(app, cors_allowed_origins="*")

# MySQL configuration
db_config = {
    'user': 'root',
    'password': 'blacklair085', # Use your password
    'host': '127.0.0.1',
    'database': 'secondhand_platform'
}

# 圖檔資料夾路徑設定
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_unique_filename(filename):
       filename = secure_filename(filename)
       name, ext = os.path.splitext(filename)
       return f"{name}_{uuid.uuid4().hex}{ext}"


@app.route('/')
def home():
    return redirect(url_for('login'))

# 登入
@app.route('/login', methods=['GET', 'POST'])
def login():
    app.logger.info("Login route accessed")
    if request.method == 'POST':
        student_id = request.form['student_id']
        password = request.form['password']
        
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM users WHERE student_id = %s", (student_id,))
            user = cursor.fetchone()
            
            if user and user['password'] == password:  # 直接比較明文密碼
                session['user_id'] = user['id']
                session['student_id'] = user['student_id']
                app.logger.info(f"User {student_id} logged in successfully")
                return redirect(url_for('index'))  # 重定向到首頁
            else:
                app.logger.warning(f"Failed login attempt for user {student_id}")
                flash('無效的學號或密碼', 'error')
                return redirect(url_for('login'))
        except mysql.connector.Error as err:
            app.logger.error(f"Database error: {err}")
            flash('發生錯誤。請稍後再試。', 'error')
            return redirect(url_for('login'))
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    
    return render_template('Login.html')

# 登出
@app.route('/logout')
def logout():
    # 清除session中的用戶信息
    session.clear()
    flash('您已成功登出', 'success')
    return redirect(url_for('login'))

# 註冊
@app.route('/register', methods=['GET', 'POST'])
def register():
    app.logger.info("Register route accessed")
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        user_name = request.form.get('user_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        department = request.form.get('department')
        confirm_password = request.form.get('confirm_password')
        
        app.logger.info(f"Received registration form for student ID: {student_id}")
        
        # 驗證所有必填字段
        if not all([student_id, user_name, email, phone, password, confirm_password, department]):
            flash('所有欄位都必須填寫', 'error')
            return redirect(url_for('register'))
        
        # 驗證電子郵件格式
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('請輸入有效的電子郵件地址', 'error')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('密碼不匹配', 'error')
            return redirect(url_for('register'))
        
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            
            # 檢查學號或電子郵件是否已存在
            cursor.execute("SELECT * FROM users WHERE student_id = %s OR email = %s", (student_id, email))
            existing_user = cursor.fetchone()
            
            if existing_user:
                flash('該學號或電子郵件已被註冊', 'error')
                return redirect(url_for('register'))
            
            # 獲取當前時間
            registration_time = datetime.now()
            
            # 插入新用戶，包括註冊時間
            cursor.execute("""
                INSERT INTO users (student_id, user_name, email, phone_number, password, department, created_at) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (student_id, user_name, email, phone, password, department, registration_time))
            conn.commit()
            app.logger.info(f"New user registered successfully: {student_id} at {registration_time}")
            flash('註冊成功！請登入。', 'success')
            return redirect(url_for('register_success'))
        except mysql.connector.Error as e:
            app.logger.error(f"MySQL error during registration: {e}")
            flash(f'註冊失敗：資料庫錯誤 - {str(e)}', 'error')
            return redirect(url_for('register'))
        except Exception as e:
            app.logger.error(f"Unexpected error during registration: {e}")
            flash(f'發生意外錯誤：{str(e)}', 'error')
            return redirect(url_for('register'))
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    
    return render_template('Register.html')

# 註冊成功
@app.route('/register_success')
def register_success():
    return render_template('Register_success.html')

# 首頁
@app.route('/')
@app.route('/index')
def index():
    app.logger.info("Rendering index page")
    return render_template('Index.html')

# 商品展示(products database -> Index) 
@app.route('/get_products')
def get_products():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # 獲取可購買的商品
        cursor.execute("""
            SELECT id, name, description, price, seller_name, category, image_path, status, created_at
            FROM products 
            WHERE status = '可購買'
            ORDER BY RAND()
        """)
        products = cursor.fetchall()
        
        # 處理圖片路徑
        for product in products:
            if product['image_path']:
                # 獲取文件名
                filename = os.path.basename(product['image_path'])
                # 使用 url_for 生成正確的 URL
                product['image_url'] = url_for('static', filename=f'uploads/{filename}')
            else:
                product['image_url'] = url_for('static', filename='images/default.jpg')
            
            # 將 created_at 轉換為字符串，以便 JSON 序列化
            product['created_at'] = product['created_at'].isoformat()
        
        return jsonify(products)
    except mysql.connector.Error as err:
        app.logger.error(f"Database error: {err}")
        return jsonify({'error': 'An error occurred while fetching products'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# 獲取使用者通知
@app.route('/get_notifications')
def get_notifications():
    if 'user_id' not in session:
        return jsonify({
            'success': False, 
            'message': '請先登入', 
            'notifications': []
        }), 401

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # 獲取用戶的通知
        cursor.execute("""
            SELECT 
                id,
                message,
                created_at,
                is_read
            FROM notifications 
            WHERE user_id = %s 
            ORDER BY created_at DESC 
            LIMIT 10
        """, (session['user_id'],))
        
        notifications = cursor.fetchall()
        
        # 處理datetime對象，轉換為字符串格式
        for notification in notifications:
            if isinstance(notification['created_at'], datetime):
                notification['created_at'] = notification['created_at'].strftime('%Y-%m-%d %H:%M:%S')

        return jsonify({
            'success': True,
            'notifications': notifications
        })

    except mysql.connector.Error as err:
        app.logger.error(f"Database error in get_notifications: {err}")
        return jsonify({
            'success': False,
            'message': '獲取通知時發生錯誤',
            'notifications': []
        }), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# 標記通知為已讀
@app.route('/mark_notification_read/<int:notification_id>', methods=['POST'])
def mark_notification_read(notification_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '請先登入'}), 401

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # 更新通知狀態
        cursor.execute("""
            UPDATE notifications 
            SET is_read = 1 
            WHERE id = %s AND user_id = %s
        """, (notification_id, session['user_id']))
        
        conn.commit()

        return jsonify({'success': True})

    except mysql.connector.Error as err:
        app.logger.error(f"Database error in mark_notification_read: {err}")
        return jsonify({'success': False, 'message': '標記通知時發生錯誤'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# 聊天室系統
@app.route('/api/chat/rooms', methods=['GET'])
def get_chat_rooms():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # 獲取用戶的所有聊天室
        cursor.execute("""
            SELECT 
                cr.id as room_id,
                cr.product_id,
                p.name as product_name,
                CASE 
                    WHEN cr.buyer_id = %s THEN seller.user_name
                    ELSE buyer.user_name
                END as other_user_name,
                (SELECT message FROM chat_messages 
                 WHERE room_id = cr.id 
                 ORDER BY created_at DESC LIMIT 1) as last_message,
                (SELECT COUNT(*) FROM chat_messages 
                 WHERE room_id = cr.id AND sender_id != %s AND is_read = FALSE) as unread_count
            FROM chat_rooms cr
            JOIN users buyer ON cr.buyer_id = buyer.id
            JOIN users seller ON cr.seller_id = seller.id
            JOIN products p ON cr.product_id = p.id
            WHERE cr.buyer_id = %s OR cr.seller_id = %s
            ORDER BY (SELECT created_at FROM chat_messages 
                     WHERE room_id = cr.id ORDER BY created_at DESC LIMIT 1) DESC
        """, (session['user_id'], session['user_id'], session['user_id'], session['user_id']))
        
        chat_rooms = cursor.fetchall()
        return jsonify(chat_rooms)
        
    except mysql.connector.Error as err:
        app.logger.error(f"Database error: {err}")
        return jsonify({'error': str(err)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/chat/messages/<int:room_id>', methods=['GET'])
def get_chat_messages(room_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # 檢查用戶是否屬於該聊天室
        cursor.execute("""
            SELECT id FROM chat_rooms 
            WHERE id = %s AND (buyer_id = %s OR seller_id = %s)
        """, (room_id, session['user_id'], session['user_id']))
        
        if not cursor.fetchone():
            return jsonify({'error': 'Forbidden'}), 403
            
        # 獲取聊天記錄
        cursor.execute("""
            SELECT 
                cm.id,
                cm.sender_id,
                cm.message,
                cm.is_read,
                cm.created_at,
                u.user_name as sender_name
            FROM chat_messages cm
            JOIN users u ON cm.sender_id = u.id
            WHERE cm.room_id = %s
            ORDER BY cm.created_at ASC
        """, (room_id,))
        
        messages = cursor.fetchall()
        
        # 處理datetime對象
        for message in messages:
            message['created_at'] = message['created_at'].isoformat()
            
        return jsonify(messages)
        
    except mysql.connector.Error as err:
        app.logger.error(f"Database error: {err}")
        return jsonify({'error': str(err)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/chat/start', methods=['POST'])
def start_chat():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.get_json()
    product_id = data.get('product_id')
    
    if not product_id:
        return jsonify({'error': 'Product ID is required'}), 400
        
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # 獲取商品和賣家信息
        cursor.execute("""
            SELECT p.id, p.seller_name, u.id as seller_id 
            FROM products p
            JOIN users u ON p.seller_name = u.user_name
            WHERE p.id = %s
        """, (product_id,))
        
        product = cursor.fetchone()
        if not product:
            return jsonify({'error': 'Product not found'}), 404
            
        # 檢查是否已存在聊天室
        cursor.execute("""
            SELECT id FROM chat_rooms 
            WHERE product_id = %s AND 
                  ((buyer_id = %s AND seller_id = %s) OR 
                   (buyer_id = %s AND seller_id = %s))
        """, (product_id, session['user_id'], product['seller_id'], 
              product['seller_id'], session['user_id']))
              
        existing_room = cursor.fetchone()
        
        if existing_room:
            return jsonify({
                'room_id': existing_room['id'],
                'seller_name': product['seller_name']
            })
            
        # 創建新聊天室
        cursor.execute("""
            INSERT INTO chat_rooms (buyer_id, seller_id, product_id)
            VALUES (%s, %s, %s)
        """, (session['user_id'], product['seller_id'], product_id))
        
        new_room_id = cursor.lastrowid
        
        conn.commit()
        
        return jsonify({
            'room_id': new_room_id,
            'seller_name': product['seller_name']
        })
        
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)
    emit('status', {'msg': f'User has joined the room.'}, room=room)

@socketio.on('leave')
def on_leave(data):
    room = data['room']
    leave_room(room)
    emit('status', {'msg': f'User has left the room.'}, room=room)

@socketio.on('message')
def handle_message(data):
    if 'user_id' not in session:
        return
        
    room_id = data.get('room')
    message = data.get('message')
    
    if not all([room_id, message]):
        return
        
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # 保存消息到數據庫
        cursor.execute("""
            INSERT INTO chat_messages (room_id, sender_id, message)
            VALUES (%s, %s, %s)
        """, (room_id, session['user_id'], message))
        
        # 獲取發送者信息
        cursor.execute("SELECT user_name FROM users WHERE id = %s", (session['user_id'],))
        sender = cursor.fetchone()
        
        conn.commit()
        
        # 廣播消息給房間內的所有用戶
        emit('message', {
            'id': cursor.lastrowid,
            'sender_id': session['user_id'],
            'sender_name': sender['user_name'],
            'message': message,
            'created_at': datetime.now().isoformat()
        }, room=room_id)
        
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN cr.buyer_id = %s THEN cr.seller_id
                    ELSE cr.buyer_id
                END as receiver_id,
                CASE 
                    WHEN cr.buyer_id = %s THEN seller.user_name
                    ELSE buyer.user_name
                END as receiver_name
            FROM chat_rooms cr
            JOIN users buyer ON cr.buyer_id = buyer.id
            JOIN users seller ON cr.seller_id = seller.id
            WHERE cr.id = %s
        """, (session['user_id'], session['user_id'], room_id))
        
        receiver = cursor.fetchone()
        
        # 插入通知
        cursor.execute("""
            INSERT INTO notifications (
                user_id,
                message,
                created_at
            ) VALUES (%s, %s, NOW())
        """, (
            receiver['receiver_id'],
            f'您收到來自 {sender["user_name"]} 的新訊息'
        ))
        
        conn.commit()
        
    except mysql.connector.Error as err:
        emit('error', {'message': str(err)})
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
            
@app.route('/api/chat/unread-count', methods=['GET'])
def get_unread_count():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM chat_messages cm
            JOIN chat_rooms cr ON cm.room_id = cr.id
            WHERE (cr.buyer_id = %s OR cr.seller_id = %s)
            AND cm.sender_id != %s
            AND cm.is_read = FALSE
        """, (session['user_id'], session['user_id'], session['user_id']))
        
        result = cursor.fetchone()
        return jsonify({'unread_count': result['count']})
        
    except mysql.connector.Error as err:
        app.logger.error(f"Database error: {err}")
        return jsonify({'error': str(err)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/chat/mark-read/<int:room_id>', methods=['POST'])
def mark_messages_read(room_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        # 更新該聊天室中所有不是由當前用戶發送的未讀消息
        cursor.execute("""
            UPDATE chat_messages 
            SET is_read = TRUE 
            WHERE room_id = %s 
            AND sender_id != %s 
            AND is_read = FALSE
        """, (room_id, session['user_id']))
        
        conn.commit()
        return jsonify({'success': True})
        
    except mysql.connector.Error as err:
        app.logger.error(f"Database error: {err}")
        return jsonify({'error': str(err)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

# 搜尋(篩選、排序)
@app.route('/search', methods=['GET'])
def search():
    # 獲取搜索參數
    query = request.args.get('q', '')
    category = request.args.get('category', 'all')
    price_min = request.args.get('price_min', '')
    price_max = request.args.get('price_max', '')
    sort_by = request.args.get('sort_by', 'relevance')

    try:
        # 轉換價格範圍為浮點數，處理空值情況
        price_min = float(price_min) if price_min.strip() else 0
        price_max = float(price_max) if price_max.strip() else float('inf')
    except ValueError:
        price_min = 0
        price_max = float('inf')

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # 構建基本查詢條件
        conditions = ["status = '可購買'"]
        params = []

        # 添加關鍵字搜索條件
        if query:
            conditions.append("(name LIKE %s OR description LIKE %s)")
            params.extend([f'%{query}%', f'%{query}%'])

        # 添加科系篩選條件
        if category != 'all':
            conditions.append("category = %s")
            params.append(category)

        # 添加價格範圍條件
        if price_min > 0:
            conditions.append("price >= %s")
            params.append(price_min)
        if price_max < float('inf'):
            conditions.append("price <= %s")
            params.append(price_max)

        # 構建排序條件
        order_by = {
            'price_asc': "price ASC",
            'price_desc': "price DESC",
            'newest': "created_at DESC",
            'relevance': "CASE WHEN name LIKE %s THEN 1 ELSE 2 END, created_at DESC"
        }

        # 構建完整的 SQL 查詢
        query_sql = f"""
            SELECT id, name, description, price, seller_name, category, image_path, status, created_at
            FROM products
            WHERE {' AND '.join(conditions)}
        """

        # 添加排序條件
        if sort_by in order_by:
            query_sql += f" ORDER BY {order_by[sort_by]}"
            if sort_by == 'relevance' and query:
                params.append(f'%{query}%')

        cursor.execute(query_sql, params)
        products = cursor.fetchall()

        # 處理圖片路徑
        for product in products:
            if product['image_path']:
                filename = os.path.basename(product['image_path'])
                product['image_url'] = url_for('static', filename=f'uploads/{filename}')
            else:
                product['image_url'] = url_for('static', filename='images/default.jpg')

        # 獲取所有可用的科系分類
        cursor.execute("""
            SELECT DISTINCT category 
            FROM products 
            WHERE category IS NOT NULL AND category != ''
            ORDER BY category
        """)
        categories = [row['category'] for row in cursor.fetchall()]

        # 添加 float 函數到模板上下文
        return render_template('Result.html',
            products=products,
            categories=categories,
            selected_category=category,
            price_min=price_min if price_min > 0 else '',
            price_max=price_max if price_max != float('inf') else '',
            sort_by=sort_by,
            query=query,
            float=float  # 明確傳遞 float 函數到模板
        )

    except mysql.connector.Error as err:
        app.logger.error(f"Database error: {err}")
        flash('發生錯誤。請稍後再試。', 'error')
        return redirect(url_for('index'))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# 商品頁
@app.route('/product/<int:product_id>')
def product_page(product_id):
    if 'user_id' not in session:
        flash('請先登入以查看商品詳情', 'error')
        return redirect(url_for('login'))
        
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # Get product and seller details
        cursor.execute("""
            SELECT p.*, u.id as seller_id, u.user_name as seller_name
            FROM products p
            JOIN users u ON p.seller_name = u.user_name
            WHERE p.id = %s
        """, (product_id,))
        
        product = cursor.fetchone()
        
        if product:
            if product['image_path']:
                filename = os.path.basename(product['image_path'])
                product['image_url'] = url_for('static', filename=f'uploads/{filename}')
            else:
                product['image_url'] = url_for('static', filename='images/default.jpg')
                
            return render_template('Product_Page.html', 
                                product=product,
                                user_id=session.get('user_id'))
        else:
            flash('商品不存在', 'error')
            return redirect(url_for('index'))
            
    except mysql.connector.Error as err:
        app.logger.error(f"Database error: {err}")
        flash('發生錯誤，請稍後再試', 'error')
        return redirect(url_for('index'))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
            
# 關於
@app.route('/about')
def about():
    app.logger.info("Rendering about page")
    return render_template('About.html')

# 上架商品
@app.route('/post_products', methods=['GET', 'POST'])
def post_products():
    app.logger.info("Post products route accessed")
    if 'user_id' not in session:
        flash('請先登入以發布商品', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        category = request.form.get('category')
        
        # Validate input
        if not all([name, description, price, category]):
            flash('所有欄位都必須填寫', 'error')
            return redirect(url_for('post_products'))

        try:
            price = int(price)
        except ValueError:
            flash('請輸入有效的價格（整數）', 'error')
            return redirect(url_for('post_products'))

        # Handle file upload
        if 'image' not in request.files:
            flash('沒有上傳圖片', 'error')
            return redirect(url_for('post_products'))
        
        file = request.files['image']
        if file.filename == '':
            flash('沒有選擇圖片', 'error')
            return redirect(url_for('post_products'))
        
        if file and allowed_file(file.filename):
            filename = get_unique_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            relative_filepath = os.path.join('uploads', filename)
        else:
            flash('不允許的文件格式', 'error')
            return redirect(url_for('post_products'))

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()

            # Get seller_name from session
            cursor.execute("SELECT user_name FROM users WHERE id = %s", (session['user_id'],))
            seller_name = cursor.fetchone()[0]

            # Insert new product
            insert_query = """
                INSERT INTO products (name, description, price, seller_name, category, image_path)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            insert_values = (name, description, price, seller_name, category, filepath)
            
            cursor.execute(insert_query, insert_values)
            conn.commit()

            app.logger.info(f"New product posted successfully: {name}")
            flash('商品發布成功！', 'success')
            return redirect(url_for('index'))
        
        except mysql.connector.Error as err:
            app.logger.error(f"Database error: {err}")
            flash('發生錯誤。請稍後再試。', 'error')
            return redirect(url_for('post_products'))
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    return render_template('Post_Products.html')

# 購物車
@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'user_id' not in session:
        return jsonify({
            'success': False,
            'message': '請先登入以使用購物車功能'
        }), 401

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # 檢查商品是否存在且可購買
        cursor.execute("""
            SELECT id, name, price, status 
            FROM products 
            WHERE id = %s AND status = '可購買'
        """, (product_id,))
        product = cursor.fetchone()

        if not product:
            return jsonify({
                'success': False,
                'message': '商品不存在或已售出'
            }), 404

        # 獲取用戶信息
        cursor.execute("SELECT user_name FROM users WHERE id = %s", (session['user_id'],))
        user = cursor.fetchone()

        # 檢查是否已在購物車中
        cursor.execute("""
            SELECT id FROM cart_items 
            WHERE user_name = %s AND product_name = %s
        """, (user['user_name'], product['name']))
        
        if cursor.fetchone():
            return jsonify({
                'success': False,
                'message': '該商品已在購物車中'
            }), 400

        # 添加到購物車
        cursor.execute("""
            INSERT INTO cart_items (user_name, product_name) 
            VALUES (%s, %s)
        """, (user['user_name'], product['name']))
        
        conn.commit()

        # 獲取購物車商品數量
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM cart_items 
            WHERE user_name = %s
        """, (user['user_name'],))
        cart_count = cursor.fetchone()['count']

        return jsonify({
            'success': True,
            'message': '商品已成功加入購物車',
            'cart_count': cart_count
        })

    except mysql.connector.Error as err:
        app.logger.error(f"Database error: {err}")
        return jsonify({
            'success': False,
            'message': '系統錯誤，請稍後再試'
        }), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/remove_from_cart/<int:item_id>', methods=['POST'])
def remove_from_cart(item_id):
    if 'user_id' not in session:
        return jsonify({
            'success': False,
            'message': '請先登入以使用購物車功能'
        }), 401

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # 刪除購物車項目
        cursor.execute("""
            DELETE FROM cart_items 
            WHERE id = %s AND user_name = (
                SELECT user_name 
                FROM users 
                WHERE id = %s
            )
        """, (item_id, session['user_id']))
        
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({
                'success': False,
                'message': '找不到指定的購物車項目'
            }), 404

        # 獲取更新後的購物車內容
        cursor.execute("""
            SELECT ci.id, ci.product_name, p.price, p.image_path
            FROM cart_items ci
            JOIN products p ON ci.product_name = p.name
            WHERE ci.user_name = (
                SELECT user_name 
                FROM users 
                WHERE id = %s
            )
        """, (session['user_id'],))
        
        cart_items = cursor.fetchall()
        total_price = sum(item['price'] for item in cart_items)

        return jsonify({
            'success': True,
            'message': '商品已成功從購物車中移除',
            'cart_items': cart_items,
            'total_price': total_price
        })

    except mysql.connector.Error as err:
        app.logger.error(f"Database error: {err}")
        return jsonify({
            'success': False,
            'message': '系統錯誤，請稍後再試'
        }), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/shopping_cart')
def shopping_cart():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # 獲取購物車內容
        cursor.execute("""
            SELECT ci.id, ci.product_name, p.price, p.image_path
            FROM cart_items ci
            JOIN products p ON ci.product_name = p.name
            WHERE ci.user_name = (
                SELECT user_name 
                FROM users 
                WHERE id = %s
            )
        """, (session['user_id'],))
        
        cart_items = cursor.fetchall()
        total_price = sum(item['price'] for item in cart_items)

        return render_template('Shopping_Cart.html', 
                            cart_items=cart_items, 
                            total_price=total_price)

    except mysql.connector.Error as err:
        app.logger.error(f"Database error: {err}")
        flash('系統錯誤，請稍後再試', 'error')
        return redirect(url_for('index'))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# 個人資料
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Please log in to view your profile', 'error')
        return redirect(url_for('login'))
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # Fetch user data
        cursor.execute("""
            SELECT u.*, 
                   COUNT(o.id) as total_orders,
                   SUM(CASE WHEN o.status = '已完成' THEN 1 ELSE 0 END) as completed_orders,
                   SUM(CASE WHEN o.status = '已取消' THEN 1 ELSE 0 END) as cancelled_orders
            FROM users u
            LEFT JOIN orders o ON u.user_name = o.buyer_name
            WHERE u.id = %s
            GROUP BY u.id
        """, (session['user_id'],))
        user = cursor.fetchone()
        
        if user:
            user['total_orders'] = user['total_orders'] or 0
            user['completed_orders'] = user['completed_orders'] or 0
            user['cancelled_orders'] = user['cancelled_orders'] or 0
            
            if user['total_orders'] > 0:
                user['completion_rate'] = round((user['completed_orders'] / user['total_orders']) * 100, 1)
            else:
                user['completion_rate'] = 0
            
            # Fetch user's products
            cursor.execute("""
                SELECT id, name, price, status, created_at
                FROM products
                WHERE seller_name = %s
                ORDER BY created_at DESC
            """, (user['user_name'],))
            user_products = cursor.fetchall()
            
            # Fetch user's orders (as buyer)
            cursor.execute("""
                SELECT o.*, p.price
                FROM orders o
                JOIN products p ON o.product_name = p.name
                WHERE o.buyer_name = %s
                ORDER BY o.created_at DESC
            """, (user['user_name'],))
            buying_orders = cursor.fetchall()
            
             # Fetch user's orders (as seller)
            cursor.execute("""
                SELECT o.*, p.price
                FROM orders o
                JOIN products p ON o.product_name = p.name
                WHERE o.seller_name = %s
                ORDER BY o.created_at DESC
            """, (user['user_name'],))
            selling_orders = cursor.fetchall()
            
            # Fetch user's notifications
            cursor.execute("""
                SELECT id, message, created_at, is_read
                FROM notifications
                WHERE user_id = %s
                ORDER BY created_at DESC
            """, (session['user_id'],))
            notifications = cursor.fetchall()
            
            return render_template('Profile.html', 
                                    user=user, 
                                    user_products=user_products,
                                    buying_orders=buying_orders,
                                    selling_orders=selling_orders, 
                                    notifications=notifications)
        else:
            flash('User not found', 'error')
            return redirect(url_for('login'))
    except mysql.connector.Error as err:
        flash('An error occurred. Please try again later.', 'error')
        return redirect(url_for('login'))
    finally:
        if 'cursor' in locals():
            cursor.close()
            
# 修改個人資料
@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        flash('請登入以編輯您的個人資料', 'error')
        return redirect(url_for('login'))
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        if request.method == 'POST':
            user_name = request.form.get('user_name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            department = request.form.get('department')
            password = request.form.get('password')
            
            app.logger.info(f"Received form data: user_name={user_name}, email={email}, phone={phone}, department={department}")
            
            # 驗證輸入
            if not all([user_name, email, phone, department]):
                flash('所有欄位都必須填寫', 'error')
                return redirect(url_for('edit_profile'))
            
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                flash('請輸入有效的電子郵件地址', 'error')
                return redirect(url_for('edit_profile'))
            
            # 更新用戶信息
            if password:
                update_query = """
                    UPDATE users 
                    SET user_name = %s, email = %s, phone_number = %s, department = %s, password = %s
                    WHERE id = %s
                """
                update_values = (user_name, email, phone, department, password, session['user_id'])
            else:
                update_query = """
                    UPDATE users 
                    SET user_name = %s, email = %s, phone_number = %s, department = %s
                    WHERE id = %s
                """
                update_values = (user_name, email, phone, department, session['user_id'])
            
            app.logger.info(f"Executing query: {update_query}")
            app.logger.info(f"Query values: {update_values}")
            
            cursor.execute(update_query, update_values)
            rows_affected = cursor.rowcount
            conn.commit()
            
            # Check if any rows were affected
            if rows_affected == 0:
                app.logger.warning("No rows were updated in the database")
                flash('No changes were made to your profile', 'warning')
            else:
                app.logger.info(f"Profile updated for user {session['user_id']}")
                flash('個人資料更新成功', 'success')
            
            # Fetch updated user data
            cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
            updated_user = cursor.fetchone()
            app.logger.info(f"Updated user data: {updated_user}")
            
            return redirect(url_for('profile'))
        
        # GET 請求：獲取當前用戶數據
        cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
        user = cursor.fetchone()
        
        return render_template('Edit_Profile.html', user=user)
    
    except mysql.connector.Error as err:
        app.logger.error(f"Database error: {err}")
        flash('發生錯誤。請稍後再試。', 'error')
        return redirect(url_for('profile'))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# 信用評分計算
def calculate_credit_score(user_name):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # 獲取用戶的訂單統計
        cursor.execute("""
            SELECT 
                COUNT(*) as total_orders,
                SUM(CASE WHEN status = '已完成' THEN 1 ELSE 0 END) as completed_orders
            FROM orders 
            WHERE buyer_name = %s
        """, (user_name,))
        
        order_stats = cursor.fetchone()
        
        # 如果沒有訂單，返回基本分數 80
        if not order_stats['total_orders']:
            return 80
            
        # 計算完成率
        completion_rate = (order_stats['completed_orders'] / order_stats['total_orders']) * 100
        
        # 根據完成率計算最終分數
        if completion_rate >= 90:
            score = min(95 + (completion_rate - 90) * 0.5, 100)  # 95-100分
        elif completion_rate >= 80:
            score = 85 + (completion_rate - 80) * 1  # 85-94分
        elif completion_rate >= 70:
            score = 75 + (completion_rate - 70) * 1  # 75-84分
        else:
            score = max(60 + completion_rate * 0.2, 60)  # 60-74分
            
        return round(score, 1)
        
    except mysql.connector.Error as err:
        app.logger.error(f"Database error in calculate_credit_score: {err}")
        return 80  # 發生錯誤時返回基本分數
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
            
@app.route('/api/transaction-stats')
def get_transaction_stats():
    if 'user_id' not in session:
        app.logger.error('User not authenticated')
        return jsonify({'error': 'Unauthorized'}), 401

    app.logger.info(f'Starting transaction stats request for user_id: {session["user_id"]}')
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # 1. 獲取用戶信息
        cursor.execute("""
            SELECT user_name, COALESCE(credit_score, 80) as credit_score 
            FROM users 
            WHERE id = %s
        """, (session['user_id'],))
        
        user = cursor.fetchone()
        if not user:
            app.logger.warning(f"No user found for id: {session['user_id']}")
            return jsonify({'error': 'User not found'}), 404
            
        user_name = user['user_name']
        
        # 準備響應數據
        response_data = {
            'creditScore': int(user['credit_score']),
            'monthly': [],
            'status': {
                'completed': 0,
                'processing': 0,
                'cancelled': 0
            },
            'summary': {
                'totalTransactions': 0,
                'totalPurchases': 0,
                'totalSales': 0,
                'avgAmount': 0
            }
        }

        # 2. 獲取月度數據 - 修正表別名
        cursor.execute("""
            SELECT 
                DATE_FORMAT(o.created_at, '%Y-%m') as month,
                COUNT(CASE WHEN o.buyer_name = %s THEN 1 END) as buying,
                COUNT(CASE WHEN o.seller_name = %s THEN 1 END) as selling
            FROM orders o
            WHERE o.created_at >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
                AND (o.buyer_name = %s OR o.seller_name = %s)
            GROUP BY DATE_FORMAT(o.created_at, '%Y-%m')
            ORDER BY month
        """, (user_name, user_name, user_name, user_name))
        
        monthly_data = cursor.fetchall()
        app.logger.info(f"Monthly data: {monthly_data}")
        
        response_data['monthly'] = [
            {
                'month': row['month'],
                'buying': int(row['buying'] or 0),
                'selling': int(row['selling'] or 0)
            } for row in monthly_data
        ]

        # 3. 獲取訂單狀態 - 修正表別名
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN o.status = '已完成' THEN 1 END) as completed,
                COUNT(CASE WHEN o.status = '未完成' THEN 1 END) as processing,
                COUNT(CASE WHEN o.status = '已取消' THEN 1 END) as cancelled
            FROM orders o
            WHERE o.buyer_name = %s OR o.seller_name = %s
        """, (user_name, user_name))
        
        status_data = cursor.fetchone()
        app.logger.info(f"Status data: {status_data}")
        
        if status_data:
            response_data['status'] = {
                'completed': int(status_data['completed'] or 0),
                'processing': int(status_data['processing'] or 0),
                'cancelled': int(status_data['cancelled'] or 0)
            }

        # 4. 獲取交易摘要 - 修正表別名和欄位引用
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT o.id) as total_transactions,
                COUNT(DISTINCT CASE WHEN o.buyer_name = %s THEN o.id END) as total_purchases,
                COUNT(DISTINCT CASE WHEN o.seller_name = %s THEN o.id END) as total_sales,
                COALESCE(AVG(p.price), 0) as avg_amount
            FROM orders o
            LEFT JOIN products p ON o.product_name = p.name
            WHERE o.buyer_name = %s OR o.seller_name = %s
        """, (user_name, user_name, user_name, user_name))
        
        summary_data = cursor.fetchone()
        app.logger.info(f"Summary data: {summary_data}")
        
        if summary_data:
            response_data['summary'] = {
                'totalTransactions': int(summary_data['total_transactions'] or 0),
                'totalPurchases': int(summary_data['total_purchases'] or 0),
                'totalSales': int(summary_data['total_sales'] or 0),
                'avgAmount': round(float(summary_data['avg_amount'] or 0), 2)
            }

        app.logger.info(f"Final response data: {response_data}")
        return jsonify(response_data)
        
    except mysql.connector.Error as err:
        app.logger.error(f"Database error: {err}")
        return jsonify({
            'error': 'Database error occurred',
            'message': str(err)
        }), 500
        
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Unexpected error occurred',
            'message': str(e)
        }), 500
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# 訂單紀錄
@app.route('/update_order_status/<int:order_id>', methods=['POST'])
def update_order_status(order_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '請先登入'}), 401
        
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if new_status not in ['已完成', '已取消']:
            return jsonify({'success': False, 'message': '無效的狀態'}), 400
            
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # 確認是否為買家
        cursor.execute("""
            SELECT o.*, u.id as user_id
            FROM orders o
            JOIN users u ON o.buyer_name = u.user_name
            WHERE o.id = %s
        """, (order_id,))
        order = cursor.fetchone()
        
        if not order or order['user_id'] != session['user_id']:
            return jsonify({'success': False, 'message': '您沒有權限更改此訂單'}), 403
            
        # 更新訂單狀態
        cursor.execute("""
            UPDATE orders 
            SET status = %s 
            WHERE id = %s
        """, (new_status, order_id))
        
        # 發送通知給賣家
        cursor.execute("""
        INSERT INTO notifications (
            user_id,
            message,
            created_at
        ) SELECT 
            u.id,
            %s,
            NOW()
        FROM users u
        WHERE u.user_name = %s
        """, (
        f'訂單 #{order_id} 已被買家標記為{new_status}',
        order['seller_name']
        ))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': f'訂單狀態已更新為{new_status}'
        })
        
    except mysql.connector.Error as err:
        app.logger.error(f"Database error: {err}")
        return jsonify({
            'success': False,
            'message': '資料庫錯誤，請稍後再試'
        }), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
            
def update_all_credit_scores():
    """定時更新所有用戶的信用分數"""
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # 獲取所有用戶
        cursor.execute("SELECT user_name FROM users")
        users = cursor.fetchall()
        
        for user in users:
            score = calculate_credit_score(user['user_name'])
            
            # 更新用戶的信用分數
            cursor.execute("""
                UPDATE users 
                SET credit_score = %d
                WHERE user_name = %s
            """, (score, user['user_name']))
            
        conn.commit()
        
    except mysql.connector.Error as err:
        app.logger.error(f"Database error in update_all_credit_scores: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# 商品管理
@app.route('/product_management/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if 'user_id' not in session:
        flash('請先登入以編輯商品', 'error')
        return redirect(url_for('login'))

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # 獲取商品信息
        cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
        product = cursor.fetchone()

        if not product:
            flash('商品不存在', 'error')
            return redirect(url_for('profile'))

        # 檢查當前用戶是否為商品的賣家
        cursor.execute("SELECT user_name FROM users WHERE id = %s", (session['user_id'],))
        current_user = cursor.fetchone()['user_name']
        if product['seller_name'] != current_user:
            flash('您沒有權限編輯此商品', 'error')
            return redirect(url_for('profile'))

        if request.method == 'POST':
            # 處理 POST 請求的邏輯
            name = request.form.get('name')
            description = request.form.get('description')
            price = request.form.get('price')
            category = request.form.get('category')
            status = request.form.get('status')

            # 更新商品信息
            update_query = """
                UPDATE products 
                SET name = %s, description = %s, price = %s, category = %s, status = %s
                WHERE id = %s
            """
            cursor.execute(update_query, (name, description, price, category, status, product_id))
            conn.commit()

            flash('商品更新成功', 'success')
            return redirect(url_for('profile'))

        return render_template('Product_Management.html', product=product)

    except mysql.connector.Error as err:
        app.logger.error(f"Database error: {err}")
        flash('發生錯誤，請稍後再試', 'error')
        return redirect(url_for('profile'))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# 結帳
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'user_id' not in session:
        flash('請先登入', 'error')
        return redirect(url_for('login'))
        
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # Get user info
        cursor.execute("""
            SELECT user_name, student_id, phone_number 
            FROM users 
            WHERE id = %s
        """, (session['user_id'],))
        user = cursor.fetchone()
        
        if request.method == 'POST':
            buyer_name = user['user_name']
            meeting_points = request.form.getlist('meeting_point[]')
            meeting_times = request.form.getlist('meeting_time[]')
            product_names = request.form.getlist('product_name[]')
            seller_names = request.form.getlist('seller_name[]')
            
            # Store purchased items info before creating orders
            cursor.execute("""
                SELECT p.name as product_name, p.price, p.image_path
                FROM products p
                WHERE p.name IN ({})
            """.format(','.join(['%s'] * len(product_names))), 
            product_names)
            purchased_items = cursor.fetchall()
            
            order_ids = []
            # Create orders...
            for i in range(len(product_names)):
                cursor.execute("""
                    INSERT INTO orders (
                        buyer_name,
                        seller_name,
                        product_name,
                        meeting_point,
                        meeting_time,
                        status
                    ) VALUES (%s, %s, %s, %s, %s, '未完成')
                """, (
                    buyer_name,
                    seller_names[i],
                    product_names[i],
                    meeting_points[i],
                    meeting_times[i]
                ))
                
                order_ids.append(cursor.lastrowid)
                
                # Update product status...
                cursor.execute("""
                    UPDATE products 
                    SET status = '已售出' 
                    WHERE name = %s
                """, (product_names[i],))
                
                # Send notifications...
                cursor.execute("""
                INSERT INTO notifications (
                    user_id,
                    message,
                    created_at
                ) VALUES (
                    %s,
                    %s,
                    NOW()
                )
            """, (
                session['user_id'],
                f'您已成功購買商品 {product_names[i]}，請在約定時間 {meeting_times[i]} 至 {meeting_points[i]} 面交'
            ))
            
            # 給賣家發送新訂單通知
            cursor.execute("""
                INSERT INTO notifications (
                    user_id,
                    message,
                    created_at
                ) SELECT 
                    u.id,
                    %s,
                    NOW()
                FROM users u
                WHERE u.user_name = %s
            """, (
                f'您有新訂單！買家 {buyer_name} 購買了商品 {product_names[i]}，面交時間：{meeting_times[i]}，地點：{meeting_points[i]}',
                seller_names[i]
            ))
            
            # Clear shopping cart
            cursor.execute("""
                DELETE FROM cart_items 
                WHERE user_name = %s
            """, (user['user_name'],))
            
            conn.commit()
            
            # Get first order details for display
            cursor.execute("""
                SELECT *
                FROM orders
                WHERE id = %s
            """, (order_ids[0],))
            order = cursor.fetchone()
            
            # Calculate total price
            total_price = sum(item['price'] for item in purchased_items)
            
            # Add total price to order info
            order['total_price'] = total_price
            
            return render_template('Order_Completion.html',
                                    order=order,
                                    items=purchased_items)
            
        # GET 請求：顯示結帳頁面
        if request.args.get('product_id'):  # 直接結帳
            product_id = request.args.get('product_id')
            cursor.execute("""
                SELECT name, seller_name, price, image_path 
                FROM products 
                WHERE id = %s AND status = '可購買'
            """, (product_id,))
            cart_items = [cursor.fetchone()]
        else:  # 從購物車結帑
            cursor.execute("""
                SELECT p.name, p.seller_name, p.price, p.image_path
                FROM cart_items ci
                JOIN products p ON ci.product_name = p.name
                WHERE ci.user_name = %s AND p.status = '可購買'
            """, (user['user_name'],))
            cart_items = cursor.fetchall()
        
        if not cart_items:
            flash('沒有可結帳的商品', 'error')
            return redirect(url_for('shopping_cart'))
            
        total_price = sum(item['price'] for item in cart_items)
        
        return render_template('Checkout.html',
            cart_items=cart_items,
            total_price=total_price,
            user=user
        )
        
    except mysql.connector.Error as err:
        app.logger.error(f"Database error: {err}")
        flash('發生錯誤，請稍後再試', 'error')
        return redirect(url_for('shopping_cart'))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.errorhandler(404)
def page_not_found(e):
    app.logger.error(f"404 error: {request.url}")
    return f"404 Not Found: {request.url}", 404

if __name__ == '__main__':
    socketio.run(app, debug=True)