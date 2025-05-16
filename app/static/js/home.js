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
let dailySalesChart;

async function updateCharts() {
    const { month_profits } = await fetchProfits();

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
                borderColor: '#1affb2',
                backgroundColor: 'rgba(26,255,178,0.1)',
                tension: 0.3,
                fill: true,
                pointRadius: 3,
                pointBackgroundColor: '#1affb2',
                pointBorderColor: '#1affb2'
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

// --- Tasks Section ---
const tasksDateInput = document.getElementById('tasksDate');
const tasksList = document.getElementById('tasksList');
const addTaskForm = document.getElementById('addTaskForm');
const addTaskMessage = document.getElementById('addTaskMessage');

// Set default date to today and fetch tasks
if (tasksDateInput) {
    tasksDateInput.valueAsDate = new Date();
    fetchAndRenderTasks();
    tasksDateInput.addEventListener('change', fetchAndRenderTasks);
}

async function fetchAndRenderTasks() {
    const date = tasksDateInput.value;
    tasksList.innerHTML = '<div class="text-gray-400">Loading...</div>';
    try {
        const resp = await fetch(`/api/tasks?date=${date}`);
        const data = await resp.json();
        if (Array.isArray(data)) {
            if (data.length === 0) {
                tasksList.innerHTML = '<div class="text-gray-400">No tasks for this day.</div>';
            } else {
                tasksList.innerHTML = data.map(task => `
                    <div class="flex items-center justify-between bg-gray-800 rounded-lg px-4 py-2">
                        <span>${task.comment}</span>
                        <button class="delete-task-btn text-red-500" data-id="${task.id}">Delete</button>
                    </div>
                `).join('');
            }
        } else {
            tasksList.innerHTML = `<div class="text-red-500">${data.error || 'Failed to load tasks.'}</div>`;
        }
    } catch {
        tasksList.innerHTML = '<div class="text-red-500">Failed to load tasks.</div>';
    }
}

// Add new task
if (addTaskForm) {
    addTaskForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        addTaskMessage.textContent = '';
        const comment = document.getElementById('taskInput').value.trim();
        const date = tasksDateInput.value;
        if (!comment) {
            addTaskMessage.textContent = 'Task cannot be empty.';
            return;
        }
        try {
            const resp = await fetch('/api/tasks', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ comment, date })
            });
            const data = await resp.json();
            if (resp.ok) {
                addTaskForm.reset();
                fetchAndRenderTasks();
            } else {
                addTaskMessage.textContent = data.error || 'Failed to add task.';
            }
        } catch {
            addTaskMessage.textContent = 'Network error.';
        }
    });
}

// Delete task
if (tasksList) {
    tasksList.addEventListener('click', async function (e) {
        if (e.target.classList.contains('delete-task-btn')) {
            const id = e.target.getAttribute('data-id');
            if (confirm('Delete this task?')) {
                try {
                    const resp = await fetch(`/api/tasks/${id}`, { method: 'DELETE' });
                    if (resp.ok) {
                        fetchAndRenderTasks();
                    }
                } catch {}
            }
        }
    });
}

// --- Initial Render ---
updateDashboard();
updateCharts();
fetchCryptoPrices();

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