document.addEventListener('DOMContentLoaded', function() {
    fetchProducts();
    // 移除 appendChatModal() 因為我們使用新的聊天系統
});

function fetchProducts() {
    axios.get('/get_products')
        .then(function (response) {
            const products = response.data;
            const gallery = document.getElementById('product-gallery');
            gallery.innerHTML = ''; // 清除現有內容

            products.forEach(function(product) {
                const productElement = createProductElement(product);
                gallery.appendChild(productElement);
            });
        })
        .catch(function (error) {
            console.error('Error fetching products:', error);
            showNotification('error', '載入商品時發生錯誤，請稍後再試。');
        });
}

function createProductElement(product) {
    const productCard = document.createElement('div');
    productCard.className = 'bg-white rounded-lg shadow-md overflow-hidden transition duration-300 ease-in-out transform hover:scale-105 hover:shadow-lg';
    
    const createdDate = new Date(product.created_at).toLocaleDateString('zh-TW');
    
    productCard.innerHTML = `
        <div class="relative">
            <img src="${product.image_url}" alt="${product.name}" class="w-full h-48 object-cover">
            ${product.status === '可購買' ? `
                <div class="absolute top-2 right-2">
                    <span class="bg-green-100 text-green-800 text-xs font-medium px-2.5 py-0.5 rounded-full">
                        可購買
                    </span>
                </div>
            ` : `
                <div class="absolute top-2 right-2">
                    <span class="bg-red-100 text-red-800 text-xs font-medium px-2.5 py-0.5 rounded-full">
                        已售出
                    </span>
                </div>
            `}
        </div>
        <div class="p-4">
            <a href="/product/${product.id}" class="block">
                <h2 class="text-xl font-semibold mb-2">${product.name}</h2>
                <p class="text-gray-600 mb-2">${product.description || '無描述'}</p>
                <p class="text-indigo-600 font-bold">NT$ ${product.price}</p>
                <p class="text-sm text-gray-500 mt-2">賣家: ${product.seller_name}</p>
                <p class="text-sm text-gray-500">類別: ${product.category || '未分類'}</p>
                <p class="text-sm text-gray-500">上架日期: ${createdDate}</p>
            </a>
        </div>
    `;

    return productCard;
}

// 處理加入購物車按鈕點擊
function handleAddToCart(event, productId) {
    event.preventDefault(); // 防止點擊事件冒泡到商品卡片的連結
    ShoppingCartService.addToCart(productId);
}

// 通知函數
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