// notification.js的完整更新版本
document.addEventListener('DOMContentLoaded', function() {
    console.log('初始化通知系統...');

    // 獲取DOM元素
    const button = document.getElementById('notificationButton');
    const dropdown = document.getElementById('notificationDropdown');
    const notificationList = document.getElementById('notificationList');
    const countBadge = document.getElementById('notificationCount');

    if (!button || !dropdown || !notificationList || !countBadge) {
        console.error('無法找到必要的DOM元素');
        return;
    }

    // 切換下拉選單
    button.addEventListener('click', function(e) {
        e.stopPropagation();
        const isHidden = dropdown.classList.contains('hidden');
        
        if (isHidden) {
            dropdown.classList.remove('hidden');
            fetchNotifications();
        } else {
            dropdown.classList.add('hidden');
        }
    });

    // 點擊外部關閉下拉選單
    document.addEventListener('click', function(e) {
        if (!button.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.classList.add('hidden');
        }
    });

    // 獲取通知
    async function fetchNotifications() {
        try {
            const response = await fetch('/get_notifications');
            console.log('Fetching notifications...');
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('Received notifications:', data);

            if (!data.success) {
                throw new Error(data.message || '獲取通知失敗');
            }

            displayNotifications(data.notifications);
            updateNotificationCount(data.notifications);

        } catch (error) {
            console.error('獲取通知時發生錯誤:', error);
            notificationList.innerHTML = `
                <div class="p-4 text-sm text-red-500">
                    載入通知時發生錯誤
                </div>
            `;
        }
    }

    // 顯示通知
    function displayNotifications(notifications) {
        console.log('Displaying notifications:', notifications);
        
        if (!notifications || notifications.length === 0) {
            notificationList.innerHTML = `
                <div class="p-4 text-sm text-gray-500 text-center">
                    目前沒有通知
                </div>
            `;
            return;
        }

        notificationList.innerHTML = notifications.map(notification => `
            <div class="notification-item p-4 hover:bg-gray-50 ${notification.is_read ? 'bg-white' : 'bg-blue-50'}"
                 data-id="${notification.id}" onclick="markNotificationRead(${notification.id})">
                <div class="text-sm ${notification.is_read ? 'text-gray-600' : 'text-gray-900'}">
                    ${notification.message}
                </div>
                <div class="text-xs text-gray-500 mt-1">
                    ${notification.created_at}
                </div>
            </div>
        `).join('');
    }

    // 更新通知計數
    function updateNotificationCount(notifications) {
        const unreadCount = notifications.filter(n => !n.is_read).length;
        console.log('Unread count:', unreadCount);
        
        if (unreadCount > 0) {
            countBadge.textContent = unreadCount;
            countBadge.classList.remove('hidden');
        } else {
            countBadge.classList.add('hidden');
        }
    }

    // 標記通知為已讀
    window.markNotificationRead = async function(notificationId) {
        try {
            const response = await fetch(`/mark_notification_read/${notificationId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (response.ok) {
                const notificationElement = document.querySelector(`[data-id="${notificationId}"]`);
                if (notificationElement) {
                    notificationElement.classList.remove('bg-blue-50');
                    notificationElement.classList.add('bg-white');
                }
                fetchNotifications(); // 重新獲取通知以更新計數
            }
        } catch (error) {
            console.error('標記通知已讀時發生錯誤:', error);
        }
    };

    // 初始加載通知
    fetchNotifications();
});