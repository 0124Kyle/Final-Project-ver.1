// 等待 DOM 完全加載
document.addEventListener('DOMContentLoaded', function() {
    const postForm = document.getElementById('postForm');
    const imageInput = document.getElementById('image');
    const imagePreview = document.getElementById('imagePreview');
    const submitBtn = document.getElementById('submitBtn');
    const successModal = document.getElementById('successModal');
    const closeModal = document.getElementById('closeModal');
    const priceInput = document.getElementById('price');

    // 確保所有元素都存在
    if (!postForm || !imageInput || !imagePreview || !submitBtn || !successModal || !closeModal || !priceInput) {
        console.error('Some elements are missing from the DOM');
        return;
    }

    // 圖片預覽功能
    function previewImage(input) {
        if (input.files && input.files[0]) {
            const reader = new FileReader();
            reader.onload = function(e) {
                imagePreview.src = e.target.result;
                imagePreview.classList.remove('hidden');
            }
            reader.readAsDataURL(input.files[0]);
        }
    }

    // 表單驗證
    function validateForm() {
        const name = document.getElementById('name').value.trim();
        const description = document.getElementById('description').value.trim();
        const price = document.getElementById('price').value;
        const category = document.getElementById('category').value;
        const image = document.getElementById('image').files[0];
        
        let isValid = true;
        const errors = [];

        // 驗證書籍名稱
        if (!name) {
            errors.push('請輸入書籍名稱');
            isValid = false;
        }

        // 驗證描述
        if (!description) {
            errors.push('請輸入書籍描述');
            isValid = false;
        }

        // 驗證價格
        if (!price || isNaN(price) || price <= 0) {
            errors.push('請輸入有效的價格');
            isValid = false;
        }

        // 驗證類別
        if (!category || category === '') {
            errors.push('請選擇書籍類別');
            isValid = false;
        }

        // 驗證圖片
        if (!image) {
            errors.push('請上傳書籍圖片');
            isValid = false;
        } else {
            const validTypes = ['image/jpeg', 'image/png', 'image/jpg', 'image/gif'];
            if (!validTypes.includes(image.type)) {
                errors.push('請上傳有效的圖片格式 (JPG, PNG, GIF)');
                isValid = false;
            }
        }

        return { isValid, errors };
    }

    // 顯示錯誤訊息
    function showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'mb-4 p-4 rounded-md bg-red-100 text-red-700 error-message';
        errorDiv.textContent = message;
        
        postForm.insertBefore(errorDiv, postForm.firstChild);
        
        // 3秒後自動移除錯誤訊息
        setTimeout(() => {
            errorDiv.remove();
        }, 3000);
    }

    // 處理表單提交
    postForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // 移除所有現有的錯誤訊息
        document.querySelectorAll('.error-message').forEach(el => el.remove());
        
        // 驗證表單
        const { isValid, errors } = validateForm();
        
        if (!isValid) {
            errors.forEach(error => showError(error));
            return;
        }
        
        // 建立 FormData 物件
        const formData = new FormData(this);
        
        try {
            // 顯示載入中狀態
            submitBtn.disabled = true;
            submitBtn.textContent = '處理中...';
            
            // 發送表單數據
            const response = await fetch('/post_products', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                // 顯示成功模態框
                successModal.classList.remove('hidden');
                
                // 清空表單
                this.reset();
                imagePreview.classList.add('hidden');
                
                // 3秒後自動關閉模態框並重定向
                setTimeout(() => {
                    successModal.classList.add('hidden');
                    window.location.href = '/index';
                }, 3000);
            } else {
                throw new Error('提交失敗');
            }
        } catch (error) {
            showError('發生錯誤，請稍後再試');
        } finally {
            // 恢復提交按鈕狀態
            submitBtn.disabled = false;
            submitBtn.textContent = '發布書籍';
        }
    });

    // 關閉成功模態框
    closeModal.addEventListener('click', function() {
        successModal.classList.add('hidden');
        window.location.href = '/index';
    });

    // 圖片上傳改變事件監聽
    imageInput.addEventListener('change', function() {
        previewImage(this);
    });

    // 價格輸入限制
    priceInput.addEventListener('input', function(e) {
        // 只允許輸入數字
        this.value = this.value.replace(/[^\d]/g, '');
    });

    // 拖放檔案上傳
    const dropZone = document.querySelector('.border-dashed');
    if (dropZone) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, highlight, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, unhighlight, false);
        });

        function highlight(e) {
            dropZone.classList.add('border-indigo-500');
        }

        function unhighlight(e) {
            dropZone.classList.remove('border-indigo-500');
        }

        dropZone.addEventListener('drop', handleDrop, false);

        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;

            if (files.length > 0) {
                imageInput.files = files;
                previewImage(imageInput);
            }
        }
    }
});