// static/js/dashboard.js

// 初始化信用評分圖表
function initializeCreditScore(score = 80) {
    console.log('Initializing credit score chart with:', score);
    const creditScoreElement = document.getElementById('creditScoreGauge');
    
    if (!creditScoreElement) {
        console.error('Credit score element not found');
        return;
    }

    const ctx = creditScoreElement.getContext('2d');  // 添加這行

    // 獲取顏色
    const getScoreColor = (score) => {
        if (score >= 90) return '#10B981';      // 綠色
        if (score >= 80) return '#3B82F6';      // 藍色
        if (score >= 70) return '#F59E0B';      // 黃色
        return '#EF4444';                       // 紅色
    };

    // 獲取評級文字
    const getScoreLabel = (score) => {
        if (score >= 90) return '優良';
        if (score >= 80) return '良好';
        if (score >= 70) return '普通';
        return '需改善';
    };

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [score, 100 - score],
                backgroundColor: [
                    getScoreColor(score),
                    '#E5E7EB'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '80%',
            circumference: 180,
            rotation: -90,
            plugins: {
                tooltip: { enabled: false },
                legend: { display: false }
            }
        }
    });

    // 更新分數顯示
    const scoreElement = document.getElementById('creditScoreText');
    const scoreLabelElement = document.getElementById('creditScoreLabel');
    if (scoreElement) {
        scoreElement.textContent = score;
        scoreElement.style.color = getScoreColor(score);
    }
    if (scoreLabelElement) {
        scoreLabelElement.textContent = getScoreLabel(score);
        scoreLabelElement.style.color = getScoreColor(score);
    }
}

// 初始化每日交易趨勢圖表
function initializeTransactionTrend(dailyData = []) {
    console.log('Initializing transaction trend chart with:', dailyData);
    const trendElement = document.getElementById('transactionTrend');
    
    if (!trendElement) {
        console.error('Transaction trend element not found');
        return;
    }

    const ctx = trendElement.getContext('2d');

    // 如果沒有數據，使用預設數據
    if (!dailyData.length) {
        dailyData = [{ day: '今天', buying: 0, selling: 0 }];
    }

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dailyData.map(item => item.day),
            datasets: [
                {
                    label: '購買數量',
                    data: dailyData.map(item => Number(item.buying) || 0),
                    backgroundColor: 'rgba(59, 130, 246, 0.8)',
                    borderColor: '#3B82F6',
                    borderWidth: 1,
                    borderRadius: 4,
                    barPercentage: 0.6
                },
                {
                    label: '販售數量', 
                    data: dailyData.map(item => Number(item.selling) || 0),
                    backgroundColor: 'rgba(16, 185, 129, 0.8)',
                    borderColor: '#10B981',
                    borderWidth: 1,
                    borderRadius: 4,
                    barPercentage: 0.6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        boxWidth: 12,
                        padding: 15,
                        font: { size: 12 }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    }
                },
                y: {
                    beginAtZero: true,
                    ticks: { stepSize: 1 }
                }
            }
        }
    });
}

// 初始化訂單完成率圓餅圖
function initializeOrderCompletion(statusData = { completed: 0, processing: 0, cancelled: 0 }) {
    console.log('Initializing order completion chart with:', statusData);
    const completionElement = document.getElementById('orderCompletion');
    
    if (!completionElement) {
        console.error('Order completion element not found');
        return;
    }

    const ctx = completionElement.getContext('2d');

    const totalOrders = statusData.completed + statusData.processing + statusData.cancelled;
    const completionRate = totalOrders > 0 ? 
        ((statusData.completed / totalOrders) * 100).toFixed(1) : 0;

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['已完成', '處理中', '已取消'],
            datasets: [{
                data: [
                    statusData.completed || 0,
                    statusData.processing || 0,
                    statusData.cancelled || 0
                ],
                backgroundColor: [
                    '#10B981',
                    '#F59E0B',
                    '#EF4444'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        boxWidth: 12,
                        padding: 10,
                        font: {
                            size: 11
                        }
                    }
                },
                title: {
                    display: true,
                    text: `訂單完成率: ${completionRate}%`,
                    font: {
                        size: 14,
                        weight: 'normal'
                    },
                    padding: {
                        bottom: 10
                    }
                }
            }
        }
    });
}

// 更新統計摘要
function updateSummary(summary = {
    totalTransactions: 0,
    totalPurchases: 0,
    totalSales: 0,
    avgAmount: 0
}) {
    console.log('Updating summary with:', summary);
    
    // 更新總交易次數
    const totalTransactions = document.getElementById('totalTransactions');
    if (totalTransactions) {
        totalTransactions.textContent = summary.totalTransactions || 0;
    }

    // 更新買入/賣出比例
    const tradeRatio = document.getElementById('tradeRatio');
    if (tradeRatio) {
        tradeRatio.textContent = `${summary.totalPurchases || 0} / ${summary.totalSales || 0}`;
    }

    // 更新平均交易金額
    const avgAmount = document.getElementById('avgAmount');
    if (avgAmount) {
        avgAmount.textContent = `NT$ ${(summary.avgAmount || 0).toFixed(0)}`;
    }
}

// 初始化儀表板
async function initializeDashboard() {
    console.log('初始化儀表板...');
    
    try {
        const response = await fetch('/api/transaction-stats');
        console.log('API 回應狀態:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP 錯誤! 狀態碼: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('收到的資料:', data);

        // 初始化各個圖表
        initializeCreditScore(data.creditScore);
        initializeTransactionTrend(data.daily); // 改用 daily 而不是 monthly
        initializeOrderCompletion(data.status);
        updateSummary(data.summary);

    } catch (error) {
        console.error('初始化儀表板時發生錯誤:', error);
        // 顯示錯誤訊息
        const dashboardElement = document.getElementById('transaction-dashboard');
        if (dashboardElement) {
            dashboardElement.innerHTML = `
                <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative">
                    <strong class="font-bold">載入失敗！</strong>
                    <span class="block sm:inline">無法載入交易資料，請稍後再試。</span>
                    <p class="text-sm">${error.message}</p>
                </div>
            `;
        }
    }
}

// 當頁面載入時初始化儀表板
document.addEventListener('DOMContentLoaded', initializeDashboard);