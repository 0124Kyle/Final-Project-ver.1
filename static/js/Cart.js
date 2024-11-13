// 購物車服務模組
const ShoppingCartService = {
    // 添加商品到購物車
    addToCart: function(productId) {
        fetch(`/add_to_cart/${productId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 顯示成功訊息
                showNotification('success', '商品已成功加入購物車！');
                // 更新購物車計數
                this.updateCartCount(data.cart_count);
            } else {
                showNotification('error', data.message || '加入購物車失敗，請稍後再試。');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('error', '發生錯誤，請稍後再試。');
        });
    },

    // 從購物車中刪除商品
    removeFromCart: function(itemId) {
        fetch(`/remove_from_cart/${itemId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 顯示成功訊息
                showNotification('success', '商品已成功從購物車中移除！');
                // 更新購物車界面
                this.updateCartUI(data.cart_items, data.total_price);
                // 更新購物車計數
                this.updateCartCount(data.cart_items.length);
            } else {
                showNotification('error', data.message || '移除商品失敗，請稍後再試。');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('error', '發生錯誤，請稍後再試。');
        });
    },

    // 更新購物車界面
    updateCartUI: function(cartItems, totalPrice) {
        const container = document.getElementById('cart-items-container');
        if (!container) return;

        if (cartItems.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    您的購物車是空的
                </div>
            `;
            return;
        }

        let html = `
            <div class="bg-white shadow-md rounded-lg overflow-hidden">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                        <tr>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">商品資訊</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">價格</th>
                            <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">操作</th>
                        </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
        `;

        cartItems.forEach(item => {
            html += `
                <tr>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="flex items-center">
                            <img src="/static/${item.image_path}" alt="${item.product_name}" class="w-16 h-16 object-cover mr-4">
                            <div class="text-sm font-medium text-gray-900">${item.product_name}</div>
                        </div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="text-sm text-gray-900">NT$ ${item.price}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-right">
                        <button onclick="ShoppingCartService.removeFromCart(${item.id})" 
                                class="text-red-600 hover:text-red-900">
                            刪除
                        </button>
                    </td>
                </tr>
            `;
        });

        html += `
                    </tbody>
                </table>
            </div>
            <div class="flex justify-end items-center mt-6 px-6 py-4 bg-gray-50">
                <div class="text-xl font-bold mr-4">
                    總計：NT$ ${totalPrice}
                </div>
                <button class="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700">
                    結帳
                </button>
            </div>
        `;

        container.innerHTML = html;
    },

    // 更新購物車計數
    updateCartCount: function(count) {
        const cartCount = document.getElementById('cartCount');
        if (cartCount) {
            cartCount.textContent = count;
            cartCount.classList.toggle('hidden', count === 0);
        }
    }
};

// 通知提示函數
function showNotification(type, message) {
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${
        type === 'success' ? 'bg-green-500' : 'bg-red-500'
    } text-white`;
    notification.textContent = message;

    document.body.appendChild(notification);

    // 3秒後自動消失
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// 將服務掛載到全局
window.ShoppingCartService = ShoppingCartService;