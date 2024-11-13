-- 創建資料庫
CREATE DATABASE IF NOT EXISTS secondhand_platform;
USE secondhand_platform;

-- 用戶表
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(8) UNIQUE NOT NULL,
    user_name VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(200) NOT NULL,
    phone_number VARCHAR(10) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    department ENUM('資料科學系','歷史學系','社會學系','英文學系','政治學系','經濟學系','法律學系','心理學系','會計學系','物理學系','化學系','數學系','企業管理學系','資訊管理學系') NOT NULL DEFAULT '資料科學系',
    credit_score INT NOT NULL DEFAULT 80,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 商品表
CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100)  UNIQUE NOT NULL,
    description TEXT,
    price INT NOT NULL,
    seller_name VARCHAR(20) NOT NULL,
    category VARCHAR(50),
    image_path VARCHAR(200),
    status ENUM('可購買', '已售出') DEFAULT '可購買',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (seller_name) REFERENCES users(user_name)
);

-- 購物車
CREATE TABLE cart_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_name VARCHAR(20) NOT NULL,
    product_name VARCHAR(100) NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_name) REFERENCES users(user_name),
    FOREIGN KEY (product_name) REFERENCES products(name)
);

-- 通知
CREATE TABLE notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    message TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN NOT NULL DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 訂單
CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    buyer_name VARCHAR(20) NOT NULL,
    seller_name VARCHAR(20) NOT NULL,
    product_name VARCHAR(100) NOT NULL,
    status ENUM('未完成', '已完成', '已取消') DEFAULT '已完成',
    meeting_point VARCHAR(20) NOT NULL,
    meeting_time DATETIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (buyer_name) REFERENCES users(user_name),
    FOREIGN KEY (seller_name) REFERENCES users(user_name),
    FOREIGN KEY (product_name) REFERENCES products(name)
);

-- 創建聊天室表
CREATE TABLE chat_rooms (
	id INT AUTO_INCREMENT PRIMARY KEY,
	buyer_id INT NOT NULL,
	seller_id INT NOT NULL,
	product_id INT NOT NULL,
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
	FOREIGN KEY (buyer_id) REFERENCES users(id),
	FOREIGN KEY (seller_id) REFERENCES users(id),
	FOREIGN KEY (product_id) REFERENCES products(id)
);

-- 創建聊天消息表
CREATE TABLE chat_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
	room_id INT NOT NULL,
	sender_id INT NOT NULL,
	message TEXT NOT NULL,
	is_read BOOLEAN DEFAULT FALSE,
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
	FOREIGN KEY (room_id) REFERENCES chat_rooms(id),
	FOREIGN KEY (sender_id) REFERENCES users(id)
);

-- Add index for better query performance
CREATE INDEX idx_chat_participants 
ON chat_messages(sender_id, receiver_id, product_id);

SELECT * FROM users;
SELECT * FROM products;
SELECT * FROM cart_items;
SELECT * FROM messages;
SELECT * FROM orders;
SELECT * FROM reviews;
SELECT * FROM search_history;