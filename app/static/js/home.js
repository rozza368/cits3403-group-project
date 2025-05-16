// Fetch profits from the backend
async function fetchProfits(year = new Date().getFullYear(), month = new Date().getMonth() + 1) {
    try {
        const response = await fetch(`/api/profits?year=${year}&month=${month}`);
        if (!response.ok) {
            console.error('Failed to fetch profits:', response.statusText);
            return { month_profits: [], last_week_profits: [] };
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching profits:', error);
        return { month_profits: [], last_week_profits: [] };
    }
}

// --- Dashboard Data Calculation ---
async function getCalendarProfits() {
    const { month_profits } = await fetchProfits();
    return month_profits;
}

async function getLastWeekProfits() {
    const { last_week_profits } = await fetchProfits();
    return last_week_profits.map(p => p.profit);
}

// --- Update Dashboard Cards ---
async function updateDashboard() {
    const todayDate = new Date();
    const year = todayDate.getFullYear();
    const month = todayDate.getMonth() + 1;
    const { month_profits } = await fetchProfits(year, month);
    const today = todayDate.getDate();

    // Today's profit
    const todayProfit = month_profits.find(p => p.day === today)?.profit || 0;

    // Calculate last week's same day profit
    const lastWeekDay = today - 7;
    let lastWeekProfit = 0;
    if (lastWeekDay > 0) {
        lastWeekProfit = month_profits.find(p => p.day === lastWeekDay)?.profit || 0;
    }

    // Calculate % change from last week (same day)
    let weekChange = 0;
    if (lastWeekProfit !== 0) {
        weekChange = ((todayProfit - lastWeekProfit) / Math.abs(lastWeekProfit) * 100).toFixed(0);
    } else if (todayProfit !== 0) {
        weekChange = 100;
    }
    document.getElementById("todayMoney").textContent = `$${todayProfit.toLocaleString()}`;
    document.getElementById("todayMoneyChange").textContent = `${weekChange >= 0 ? "+" : ""}${weekChange}% vs last week`;
    document.getElementById("todayMoneyChange").className = `text-${weekChange >= 0 ? "green" : "red"}-600 text-sm mt-2`;

    // Total earnings for current month up to today
    const totalEarnings = month_profits.reduce((sum, p) => sum + p.profit, 0);
    document.getElementById("totalEarnings").textContent = `$${totalEarnings.toLocaleString()}`;

    // Calculate same period last month
    const prevMonthDate = new Date(todayDate.getFullYear(), todayDate.getMonth() - 1, 1);
    const prevMonth = prevMonthDate.getMonth() + 1;
    const prevYear = prevMonthDate.getFullYear();

    const prevMonthTrades = await fetch(`/api/profits?year=${prevYear}&month=${prevMonth}`);
    const prevMonthProfits = (await prevMonthTrades.json()).month_profits || [];

    const prevMonthEarnings = prevMonthProfits.reduce((sum, p) => sum + p.profit, 0);
    let monthChange = 0;
    if (prevMonthEarnings !== 0) {
        monthChange = ((totalEarnings - prevMonthEarnings) / Math.abs(prevMonthEarnings) * 100).toFixed(0);
    } else if (totalEarnings !== 0) {
        monthChange = 100;
    }

    // Show change or fallback message
    if (prevMonthEarnings !== 0 || totalEarnings !== 0) {
        document.getElementById("totalEarningsChange").textContent = `${monthChange >= 0 ? "+" : ""}${monthChange}% vs same period last month`;
        document.getElementById("totalEarningsChange").className = `text-${monthChange >= 0 ? "green" : "red"}-600 text-sm mt-2`;
    } else {
        document.getElementById("totalEarningsChange").textContent = "No data for previous month";
        document.getElementById("totalEarningsChange").className = "text-gray-500 text-sm mt-2";
    }
}

async function fetchUserList() {
    try {
        const response = await fetch('/api/user_list');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const userList = await response.json();
        return userList;
    } catch (error) {
        console.error('Failed to fetch user list:', error);
        return null;
    }
}

// --- Chart.js Graphs ---
let websiteViewChart, dailySalesChart, completedTasksChart;

async function updateCharts() {
    const { last_week_profits, month_profits } = await fetchProfits();

    // Website View: Bar chart for last 7 days
    const weekLabels = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];
    if (websiteViewChart) websiteViewChart.destroy();
    websiteViewChart = new Chart(document.getElementById('websiteViewChart').getContext('2d'), {
        type: 'bar',
        data: {
            labels: weekLabels,
            datasets: [{
                label: 'Profit',
                data: last_week_profits,
                backgroundColor: '#4ade80',
                borderRadius: 6,
            }]
        },
        options: {
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
        }
    });

    // Daily Sales: Line chart for each month
    const monthLabels = month_profits.map(p => p.day);
    const monthProfits = month_profits.map(p => p.profit);
    if (dailySalesChart) dailySalesChart.destroy();
    dailySalesChart = new Chart(document.getElementById('dailySalesChart').getContext('2d'), {
        type: 'line',
        data: {
            labels: monthLabels,
            datasets: [{
                label: 'Sales',
                data: monthProfits,
                borderColor: '#1affb2', // changed from '#3b82f6'
                backgroundColor: 'rgba(26,255,178,0.1)', // subtle fill
                tension: 0.3,
                fill: true,
                pointRadius: 3,
                pointBackgroundColor: '#1affb2', // changed from '#3b82f6'
                pointBorderColor: '#1affb2' // changed from '#3b82f6'
            }]
        },
        options: {
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
        }
    });
}

// --- Crypto Prices API ---
async function fetchCryptoPrices() {
    const coins = [
        { id: 'bitcoin', label: 'btc-price' },
        { id: 'ethereum', label: 'eth-price' },
        { id: 'solana', label: 'sol-price' },
        { id: 'binancecoin', label: 'bnb-price' },
        { id: 'cardano', label: 'ada-price' },
        { id: 'dogecoin', label: 'doge-price' }
    ];
    const vs_currency = 'usd';
    try {
        const resp = await fetch(`https://api.coingecko.com/api/v3/simple/price?ids=${coins.map(c => c.id).join(',')}&vs_currencies=${vs_currency}`);
        const data = await resp.json();
        coins.forEach(coin => {
            const price = data[coin.id]?.usd;
            const el = document.getElementById(coin.label);
            if (el) {
                el.textContent = price !== undefined ? `$${price.toLocaleString()}` : '$--';
            }
        });
    } catch (e) {
        // Show error in all price fields
        coins.forEach(coin => {
            const el = document.getElementById(coin.label);
            if (el) el.textContent = 'Error';
        });
    }
}

// --- Initial Render ---
updateDashboard();
updateCharts();
fetchCryptoPrices();

// --- Listen for changes in localStorage (from calendar) ---
window.addEventListener('storage', () => {
    updateDashboard();
    updateCharts();
});

// Optionally refresh crypto prices every 10 minutes
setInterval(fetchCryptoPrices, 600000); // 10 minutes

// Display list of users upon clicking on search bar
document.getElementById('usernameSearch').addEventListener('focus', async function () {
    const userListResult = await fetchUserList();
    const userList = userListResult["users"];
    const dropdown = document.getElementById('username-search-dropdown');

    if (userList && userList.length > 0) {
        dropdown.innerHTML = userList.map(user => `
            <div class="px-4 py-2 hover:bg-gray-100 cursor-pointer search-item">
                <div class="text-sm text-gray-700">${user}</div>
            </div>
        `).join('');
    } else {
        dropdown.innerHTML = '<div class="px-4 py-2 text-sm text-gray-500 search-item">No users found</div>';
    }
    dropdown.classList.remove('hidden');
});

// Filter dropdown menu based on search bar input
document.getElementById('usernameSearch').addEventListener('input', function () {
    const searchTerm = this.value.toLowerCase();
    const dropdown = document.getElementById('username-search-dropdown');
    const items = dropdown.querySelectorAll('.search-item');

    items.forEach(item => {
        const userName = item.textContent.toLowerCase();
        if (userName.includes(searchTerm)) {
            item.classList.remove('hidden');
        } else {
            item.classList.add('hidden');
        }
    });
});

// Insert clicked username into the input field
document.getElementById('username-search-dropdown').addEventListener('click', function (e) {
    const target = e.target.closest('.search-item');
    if (target && target.textContent) {
        document.getElementById('usernameSearch').value = target.textContent.trim();
        this.classList.add('hidden');
    }
});

// Close search bar dropdown when clicking outside
document.addEventListener('click', function (e) {
    const searchBar = document.getElementById('usernameSearch');
    const dropdown = document.getElementById('username-search-dropdown');
    if (!searchBar.contains(e.target)) {
        dropdown.classList.add('hidden');
    }
});

// Sharing profits section
const shareProfitBtn = document.getElementById('shareProfitBtn');
const shareProfitDialog = document.getElementById('shareProfitDialog');
const closeShareProfitDialog = document.getElementById('closeShareProfitDialog');
const shareProfitForm = document.getElementById('shareProfitForm');
const shareProfitMessage = document.getElementById('shareProfitMessage');

const dateFrom = document.getElementById('dateFrom').value;
const dateTo = document.getElementById('dateTo').value;

shareProfitBtn.addEventListener('click', () => {
    shareProfitDialog.classList.remove('hidden');
    shareProfitMessage.textContent = '';
    shareProfitForm.reset();
});

closeShareProfitDialog.addEventListener('click', () => {
    shareProfitDialog.classList.add('hidden');
});

shareProfitDialog.addEventListener('click', (e) => {
    if (e.target === shareProfitDialog) {
        shareProfitDialog.classList.add('hidden');
    }
});

shareProfitForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const dateFrom = document.getElementById('dateFrom').value;
    const dateTo = document.getElementById('dateTo').value;
    const username = document.getElementById('usernameSearch').value;

    try {
        const response = await fetch('/api/create_image', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                date_from: dateFrom,
                date_to: dateTo,
                share: username
            })
        });
        if (response.ok) {
            shareProfitMessage.textContent = 'Profit info shared successfully!';
            shareProfitMessage.className = 'mt-3 text-green-600 text-sm';
            setTimeout(() => shareProfitDialog.classList.add('hidden'), 1200);
        } else {
            shareProfitMessage.textContent = 'Failed to share profit info.';
            shareProfitMessage.className = 'mt-3 text-red-600 text-sm';
        }
    } catch {
        shareProfitMessage.textContent = 'Network error.';
        shareProfitMessage.className = 'mt-3 text-red-600 text-sm';
    }
});

document.addEventListener('DOMContentLoaded', function () {
// --- Chart.js Graphs: Improved Styles ---
// Website View Chart
if (window.websiteViewChart) window.websiteViewChart.destroy();
fetch('/api/entry')
    .then(res => res.json())
    .then(data => {
    const ctx = document.getElementById('websiteViewChart').getContext('2d');
    window.websiteViewChart = new Chart(ctx, {
        type: 'line',
        data: {
        labels: data.labels || ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        datasets: [{
            label: 'Views',
            data: data.views || [120, 190, 300, 500, 200, 300, 400],
            borderColor: '#3b82f6',
            backgroundColor: ctx.createLinearGradient(0, 0, 0, 200),
            pointBackgroundColor: '#fff',
            pointBorderColor: '#3b82f6',
            pointRadius: 5,
            fill: true,
            tension: 0.4
        }]
        },
        options: {
        plugins: {
            legend: { display: false },
            tooltip: {
            backgroundColor: '#3b82f6',
            titleColor: '#fff',
            bodyColor: '#fff',
            borderColor: '#fff',
            borderWidth: 1
            }
        },
        scales: {
            x: { grid: { display: false }, ticks: { color: '#64748b' } },
            y: { grid: { color: '#e0e7ef' }, ticks: { color: '#64748b' }, beginAtZero: true }
        }
        }
    });
    });

// Daily Sales Chart
if (window.dailySalesChart) window.dailySalesChart.destroy();
fetch('/api/profits')
    .then(res => res.json())
    .then(data => {
    const ctx = document.getElementById('dailySalesChart').getContext('2d');
    window.dailySalesChart = new Chart(ctx, {
        type: 'bar',
        data: {
        labels: data.labels || ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        datasets: [{
            label: 'Sales',
            data: data.sales || [12, 19, 3, 5, 2, 3, 7],
            backgroundColor: [
            '#34d399', '#60a5fa', '#818cf8', '#fbbf24', '#f87171', '#38bdf8', '#a78bfa'
            ],
            borderRadius: 8,
            barPercentage: 0.6
        }]
        },
        options: {
        plugins: {
            legend: { display: false },
            tooltip: {
            backgroundColor: '#10b981',
            titleColor: '#fff',
            bodyColor: '#fff',
            borderColor: '#fff',
            borderWidth: 1
            }
        },
        scales: {
            x: { grid: { display: false }, ticks: { color: '#64748b' } },
            y: { grid: { color: '#e0e7ef' }, ticks: { color: '#64748b' }, beginAtZero: true }
        }
        }
    });
    });

// Completed Tasks Chart
if (window.completedTasksChart) window.completedTasksChart.destroy();
fetch('/api/entry')
    .then(res => res.json())
    .then(data => {
    const ctx = document.getElementById('completedTasksChart').getContext('2d');
    window.completedTasksChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
        labels: ['Completed', 'Pending'],
        datasets: [{
            data: data.completed || [75, 25],
            backgroundColor: ['#a78bfa', '#e0e7ef'],
            borderWidth: 2,
            borderColor: '#fff'
        }]
        },
        options: {
        plugins: {
            legend: {
            display: true,
            position: 'bottom',
            labels: { color: '#64748b', font: { weight: 'bold' } }
            },
            tooltip: {
            backgroundColor: '#a78bfa',
            titleColor: '#fff',
            bodyColor: '#fff',
            borderColor: '#fff',
            borderWidth: 1
            }
        },
        cutout: '70%'
        }
    });
    });

// Fetch crypto prices and update the table
async function fetchCryptoPricesTable() {
    try {
    const res = await fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,binancecoin,cardano,dogecoin&vs_currencies=usd');
    if (!res.ok) throw new Error('Price fetch failed');
    const data = await res.json();
    document.getElementById('btc-price').textContent = `$${Number(data.bitcoin.usd).toLocaleString()}`;
    document.getElementById('eth-price').textContent = `$${Number(data.ethereum.usd).toLocaleString()}`;
    document.getElementById('sol-price').textContent = `$${Number(data.solana.usd).toLocaleString()}`;
    document.getElementById('bnb-price').textContent = `$${Number(data.binancecoin.usd).toLocaleString()}`;
    document.getElementById('ada-price').textContent = `$${Number(data.cardano.usd).toLocaleString()}`;
    document.getElementById('doge-price').textContent = `$${Number(data.dogecoin.usd).toLocaleString()}`;
    } catch (e) {
    document.getElementById('cryptoPricesTable').innerHTML = '<div class="text-red-500 text-center">Unable to load prices at this time.</div>';
    }
}
fetchCryptoPricesTable();
setInterval(fetchCryptoPricesTable, 60000);
});