// 全局變量
let currentRoomId = null;
let socket = null;

function initializeSocket() {
    if (!socket) {
        try {
            socket = io();
            initializeSocketEvents();
            return socket;
        } catch (error) {
            console.error('Error initializing socket:', error);
            return null;
        }
    }
    return socket;
}

// 初始化聊天系統
document.addEventListener('DOMContentLoaded', () => {
    // 初始化 Socket.IO
    initializeSocket();
    
    // 設置事件監聽器
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }

    const chatButton = document.getElementById('chatButton');
    if (chatButton) {
        chatButton.addEventListener('click', toggleChatList);
    }

    // 初始化未讀計數
    updateUnreadCount();
});

// 初始化 Socket.IO
function initializeSocketEvents() {
    if (!socket) return;

    // 移除舊的事件監聽器
    socket.off('connect');
    socket.off('message');
    socket.off('disconnect');
    socket.off('connect_error');

    // 添加新的事件監聽器
    socket.on('connect', () => {
        console.log('Connected to WebSocket server');
    });

    socket.on('message', (data) => {
        handleNewMessage(data);
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from WebSocket server');
    });

    socket.on('connect_error', (error) => {
        console.error('Connection error:', error);
    });
}

// UI 控制函數
function toggleChatList() {
    const chatButton = document.getElementById('chatButton');
    const chatList = document.getElementById('chatList');
    const chatWindow = document.getElementById('chatWindow');

    chatWindow.classList.add('hidden');
    chatButton.classList.add('hidden');
    chatList.classList.remove('hidden');
    
    loadChatRooms();
}

function closeChatList() {
    const chatButton = document.getElementById('chatButton');
    const chatList = document.getElementById('chatList');
    
    chatList.classList.add('hidden');
    chatButton.classList.remove('hidden');
}

function closeChat() {
    const chatButton = document.getElementById('chatButton');
    const chatWindow = document.getElementById('chatWindow');
    
    chatWindow.classList.add('hidden');
    chatButton.classList.remove('hidden');
    
    if (currentRoomId && socket) {
        socket.emit('leave', { room: currentRoomId });
        currentRoomId = null;
    }
}

function backToList() {
    const chatList = document.getElementById('chatList');
    const chatWindow = document.getElementById('chatWindow');
    
    if (currentRoomId && socket) {
        socket.emit('leave', { room: currentRoomId });
        currentRoomId = null;
    }
    
    chatWindow.classList.add('hidden');
    chatList.classList.remove('hidden');
}

function appendMessage(data) {
    const messageId = data.id || `temp-${Date.now()}`;
    const isTemp = messageId.toString().startsWith('temp-');
    const chatMessages = document.getElementById('chatMessages');

    // 檢查消息是否已存在
    if (!isTemp) {
        const existingMessage = document.querySelector(`[data-message-id="${messageId}"]`);
        if (existingMessage) {
            return;
        }
    }

    const messageDiv = document.createElement('div');
    const currentUserId = parseInt(document.body.getAttribute('data-user-id'));
    const isCurrentUser = data.sender_id === currentUserId;
    const isSystemMessage = data.is_system;

    if (isSystemMessage) {
        messageDiv.className = 'flex justify-center my-4';
        messageDiv.innerHTML = `
            <div class="bg-gray-100 text-gray-600 text-xs px-3 py-1 rounded-full">
                ${escapeHtml(data.message)}
            </div>
        `;
    } else {
        messageDiv.className = `flex flex-col mb-4 ${isCurrentUser ? 'items-end' : 'items-start'}`;
        messageDiv.setAttribute('data-message-id', messageId);
        
        messageDiv.innerHTML = `
            <div class="max-w-[70%]">
                <div class="px-4 py-2 rounded-lg ${
                    isCurrentUser 
                        ? 'bg-indigo-600 text-white rounded-br-none' 
                        : 'bg-gray-200 text-gray-800 rounded-bl-none'
                }">
                    <span class="message-text">${escapeHtml(data.message)}</span>
                    ${isCurrentUser ? `
                        <span class="ml-2 opacity-70 inline-flex">
                            ${isTemp ? `
                                <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                    <polyline points="20 6 9 17 4 12"></polyline>
                                </svg>
                            ` : `
                                <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                    <polyline points="20 6 9 17 4 12"></polyline>
                                    <polyline points="20 12 9 23 4 18"></polyline>
                                </svg>
                            `}
                        </span>
                    ` : ''}
                </div>
                <div class="text-xs text-gray-500 mt-1">
                    ${formatTime(data.created_at)}
                </div>
            </div>
        `;
    }
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function formatTime(timestamp) {
    if (!timestamp) {
        return new Date().toLocaleTimeString('zh-TW', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }
    const date = new Date(timestamp);
    return date.toLocaleTimeString('zh-TW', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

// API 操作函數
async function loadChatRooms() {
    try {
        const response = await fetch('/api/chat/rooms');
        if (!response.ok) throw new Error('Failed to load chat rooms');
        
        const rooms = await response.json();
        const chatRoomList = document.getElementById('chatRoomList');
        chatRoomList.innerHTML = '';
        
        rooms.forEach(room => {
            const roomDiv = document.createElement('div');
            roomDiv.className = 'p-4 border-b hover:bg-gray-50 cursor-pointer';
            roomDiv.onclick = () => openChat(room.room_id, room.other_user_name);
            
            roomDiv.innerHTML = `
                <div class="flex justify-between items-start">
                    <div>
                        <h4 class="font-medium">${room.other_user_name}</h4>
                        <p class="text-sm text-gray-500">${room.last_message || '開始聊天'}</p>
                    </div>
                    ${room.unread_count > 0 ? `
                        <span class="bg-red-500 text-white text-xs px-2 py-1 rounded-full">
                            ${room.unread_count}
                        </span>
                    ` : ''}
                </div>
            `;
            
            chatRoomList.appendChild(roomDiv);
        });
    } catch (error) {
        console.error('Error loading chat rooms:', error);
    }
}

// 更新未讀消息計數
async function updateUnreadCount() {
    try {
        const response = await fetch('/api/chat/unread-count');
        if (!response.ok) {
            throw new Error('Failed to fetch unread count');
        }
        
        const data = await response.json();
        const badge = document.getElementById('totalUnreadBadge');
        
        if (badge) {
            if (data.unread_count > 0) {
                badge.textContent = data.unread_count > 99 ? '99+' : data.unread_count;
                badge.classList.remove('hidden');
            } else {
                badge.classList.add('hidden');
            }
        }
    } catch (error) {
        console.error('Error updating unread count:', error);
    }
}

async function startChat(productId, sellerName) {
    try {
        // 確保 Socket.IO 已初始化
        if (!socket) {
            initializeSocket();
        }

        // 發送請求創建或獲取聊天室
        const response = await fetch('/api/chat/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ product_id: productId })
        });

        if (!response.ok) {
            throw new Error('Failed to start chat');
        }

        const data = await response.json();
        
        if (data.room_id) {
            // 隱藏聊天按鈕
            const chatButton = document.getElementById('chatButton');
            if (chatButton) {
                chatButton.classList.add('hidden');
            }

            // 打開聊天窗口
            await openChat(data.room_id, sellerName || data.seller_name);

            // 如果是新的聊天，添加系統消息
            if (data.is_new_chat) {
                appendMessage({
                    id: `system-${Date.now()}`,
                    sender_id: null,
                    message: `您已開始與 ${sellerName || data.seller_name} 的對話`,
                    created_at: new Date().toISOString(),
                    is_system: true
                });
            }
        }
    } catch (error) {
        console.error('Error starting chat:', error);
        alert('無法開始聊天，請稍後再試');
    }
}

async function openChat(roomId, userName) {
    try {
        // 設置當前聊天室ID
        currentRoomId = roomId;
        
        // 獲取UI元素
        const chatWindow = document.getElementById('chatWindow');
        const chatList = document.getElementById('chatList');
        const chatTitle = document.getElementById('chatTitle');
        const chatMessages = document.getElementById('chatMessages');
        const messageInput = document.getElementById('messageInput');
        
        // 設置聊天室標題
        chatTitle.textContent = userName;
        
        // 隱藏聊天列表，顯示聊天窗口
        chatList.classList.add('hidden');
        chatWindow.classList.remove('hidden');
        
        // 清空消息區域
        chatMessages.innerHTML = '';

        // 加入Socket.IO房間
        if (socket) {
            socket.emit('join', { room: roomId });
        }

        // 載入歷史消息
        const response = await fetch(`/api/chat/messages/${roomId}`);
        if (!response.ok) {
            throw new Error('Failed to load messages');
        }

        const messages = await response.json();
        
        // 按時間順序顯示消息
        messages.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
        messages.forEach(message => {
            appendMessage(message);
        });

        // 滾動到最新消息
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // 聚焦到輸入框
        if (messageInput) {
            messageInput.focus();
        }
        
        // 標記消息為已讀
        try {
            await fetch(`/api/chat/mark-read/${roomId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            // 更新未讀計數
            updateUnreadCount();
        } catch (error) {
            console.error('Error marking messages as read:', error);
        }

    } catch (error) {
        console.error('Error opening chat:', error);
    }
}

function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    
    if (!message || !currentRoomId || !socket) return;
    
    // 清空輸入框
    messageInput.value = '';
    
    // 創建臨時消息對象
    const tempMessage = {
        id: `temp-${Date.now()}`, // 確保設置了 id
        sender_id: parseInt(document.body.getAttribute('data-user-id')),
        message: message,
        created_at: new Date().toISOString()
    };
    
    // 立即顯示消息
    appendMessage(tempMessage);
    
    // 發送到服務器
    socket.emit('message', {
        room: currentRoomId,
        message: message
    });
}

function handleNewMessage(data) {
    const currentUserId = parseInt(document.body.getAttribute('data-user-id'));
    
    if (data.sender_id !== currentUserId) {
        if (document.getElementById('chatWindow').classList.contains('hidden') || 
            currentRoomId !== data.room_id) {
            updateUnreadCount();
        }
    }
    
    // 確保消息有 id
    if (!data.id) {
        data.id = `server-${Date.now()}`;
    }
    
    if (currentRoomId === data.room_id) {
        appendMessage(data);
    }
}

setInterval(() => {
    const chatList = document.getElementById('chatList');
    if (chatList && chatList.style.display === 'block') {
        loadChatRooms();
    }
    updateUnreadCount();
}, 30000);