// Fetch profits from the backend
async function fetchProfits() {
    try {
        const response = await fetch('/api/profits');
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
    const { month_profits } = await fetchProfits();
    const todayDate = new Date();
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
    const profit = document.getElementById('profitInput').value;
    const comment = document.getElementById('commentInput').value;
    const username = document.getElementById('usernameSearch').value;

    try {
        const params = new URLSearchParams({
            amount: parseInt(profit, 10),
            date_range: comment,
            share: username
        });
        const response = await fetch(`/api/create_image?${params.toString()}`, {
            method: 'GET'
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