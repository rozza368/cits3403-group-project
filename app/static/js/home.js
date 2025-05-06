// --- Dashboard Data Calculation ---
function getCalendarProfits() {
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth() + 1;
    let profits = [];
    for (let day = 1; day <= 31; day++) {
    const key = `entry-${year}-${month}-${day}-profit`;
    const val = localStorage.getItem(key);
    if (val !== null) profits.push({ day, profit: parseFloat(val) });
    }
    return profits;
}

function getLastWeekProfits() {
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth() + 1;
    let profits = [];
    const today = now.getDate();
    for (let i = 6; i >= 0; i--) {
    const day = today - i;
    if (day > 0) {
        const key = `entry-${year}-${month}-${day}-profit`;
        const val = localStorage.getItem(key);
        profits.push(val ? parseFloat(val) : 0);
    }
    }
    return profits;
}

// --- Update Dashboard Cards ---
function updateDashboard() {
    const profits = getCalendarProfits();
    const todayDate = new Date();
    const today = todayDate.getDate();
    const month = todayDate.getMonth() + 1;
    const year = todayDate.getFullYear();

    // Today's profit
    const todayProfit = profits.find(p => p.day === today)?.profit || 0;

    // Calculate last week's same day profit
    const lastWeekDay = today - 7;
    let lastWeekProfit = 0;
    if (lastWeekDay > 0) {
    const key = `entry-${year}-${month}-${lastWeekDay}-profit`;
    const val = localStorage.getItem(key);
    lastWeekProfit = val ? parseFloat(val) : 0;
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
    let totalEarnings = 0;
    for (let d = 1; d <= today; d++) {
    const key = `entry-${year}-${month}-${d}-profit`;
    const val = localStorage.getItem(key);
    if (val) totalEarnings += parseFloat(val);
    }
    document.getElementById("totalEarnings").textContent = `$${totalEarnings.toLocaleString()}`;

    // Calculate same period last month
    let prevMonth = month - 1;
    let prevYear = year;
    if (prevMonth === 0) {
    prevMonth = 12;
    prevYear = year - 1;
    }
    let prevMonthEarnings = 0;
    for (let d = 1; d <= today; d++) {
    const key = `entry-${prevYear}-${prevMonth}-${d}-profit`;
    const val = localStorage.getItem(key);
    if (val) prevMonthEarnings += parseFloat(val);
    }
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

function updateCharts() {
    const profits = getCalendarProfits();
    const now = new Date();
    const daysInMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();

    // Website View: Bar chart for last 7 days
    const lastWeek = getLastWeekProfits();
    const weekLabels = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];
    if (websiteViewChart) websiteViewChart.destroy();
    websiteViewChart = new Chart(document.getElementById('websiteViewChart').getContext('2d'), {
    type: 'bar',
    data: {
        labels: weekLabels,
        datasets: [{
        label: 'Profit',
        data: lastWeek,
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
    let monthLabels = [];
    let monthProfits = [];
    for (let m = 0; m < 12; m++) {
    let sum = 0;
    for (let d = 1; d <= 31; d++) {
        const key = `entry-${now.getFullYear()}-${m + 1}-${d}-profit`;
        const val = localStorage.getItem(key);
        if (val) sum += parseFloat(val);
    }
    monthLabels.push(['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][m]);
    monthProfits.push(sum);
    }
    if (dailySalesChart) dailySalesChart.destroy();
    dailySalesChart = new Chart(document.getElementById('dailySalesChart').getContext('2d'), {
    type: 'line',
    data: {
        labels: monthLabels,
        datasets: [{
        label: 'Sales',
        data: monthProfits,
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59,130,246,0.1)',
        tension: 0.3,
        fill: true,
        pointRadius: 3,
        pointBackgroundColor: '#3b82f6'
        }]
    },
    options: {
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true } }
    }
    });

    // Completed Tasks: Line chart for current month
    let dayLabels = [];
    let dayProfits = [];
    for (let d = 1; d <= daysInMonth; d++) {
    dayLabels.push(d);
    const key = `entry-${now.getFullYear()}-${now.getMonth() + 1}-${d}-profit`;
    const val = localStorage.getItem(key);
    dayProfits.push(val ? parseFloat(val) : 0);
    }
    if (completedTasksChart) completedTasksChart.destroy();
    completedTasksChart = new Chart(document.getElementById('completedTasksChart').getContext('2d'), {
    type: 'line',
    data: {
        labels: dayLabels,
        datasets: [{
        label: 'Completed Tasks',
        data: dayProfits,
        borderColor: '#22c55e',
        backgroundColor: 'rgba(34,197,94,0.1)',
        tension: 0.3,
        fill: true,
        pointRadius: 2,
        pointBackgroundColor: '#22c55e'
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
    const coins = ['bitcoin', 'ethereum', 'solana', 'dogecoin', 'binancecoin'];
    const vs_currency = 'usd';
    try {
    const resp = await fetch(`https://api.coingecko.com/api/v3/simple/price?ids=${coins.join(',')}&vs_currencies=${vs_currency}`);
    const data = await resp.json();
    const cryptoPricesDiv = document.getElementById('cryptoPrices');
    cryptoPricesDiv.innerHTML = '';
    coins.forEach(coin => {
        const price = data[coin]?.usd;
        if (price !== undefined) {
        const name = coin.charAt(0).toUpperCase() + coin.slice(1);
        cryptoPricesDiv.innerHTML += `
            <div class="flex justify-between items-center">
            <span class="font-semibold">${name}</span>
            <span class="text-blue-600 font-mono">$${price.toLocaleString()}</span>
            </div>
        `;
        }
    });
    } catch (e) {
    document.getElementById('cryptoPrices').innerHTML = '<span class="text-red-500">Failed to load prices.</span>';
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

// Optionally refresh crypto prices every 60 seconds
setInterval(fetchCryptoPrices, 60000);

// Display list of users upon clicking on search bar
document.getElementById('search-bar-top').addEventListener('focus', async function() {
    const userListResult = await fetchUserList();
    const userList = userListResult["users"];
    const dropdown = document.getElementById('search-dropdown');

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
document.getElementById('search-bar-top').addEventListener('input', function() {
    const searchTerm = this.value.toLowerCase();
    const dropdown = document.getElementById('search-dropdown');
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

// Close search bar dropdown when clicking outside
document.addEventListener('click', function(e) {
    const searchBar = document.getElementById('search-bar-top');
    const dropdown = document.getElementById('search-dropdown');
    if (!searchBar.contains(e.target)) {
        dropdown.classList.add('hidden');
    }
});
