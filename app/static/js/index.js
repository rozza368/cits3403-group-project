const monthYear = document.getElementById("monthYear");
const prevMonthBtn = document.getElementById("prevMonthBtn");
const nextMonthBtn = document.getElementById("nextMonthBtn");
const calendarGrid = document.getElementById("calendarGrid");

const today = new Date();
const currentMonth = today.getMonth();
const currentYear = today.getFullYear();

const urlParams = new URLSearchParams(window.location.search);
const viewMonth = parseInt(urlParams.get("month")) || currentMonth + 1;
const viewYear = parseInt(urlParams.get("year")) || currentYear;
let viewingDate = new Date(viewYear, viewMonth - 1, 1);

const monthNames = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
];

async function fetchProfits(year, month) {
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

async function renderCalendar(date) {
    calendarGrid.innerHTML = "";

    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1).getDay();
    const lastDate = new Date(year, month + 1, 0).getDate();

    const prevMonthDate = new Date(year, month, 0);
    const prevMonthLastDate = prevMonthDate.getDate();
    const prevMonth = prevMonthDate.getMonth();
    const prevMonthYear = prevMonthDate.getFullYear();

    const nextMonthDate = new Date(year, month + 1, 1);
    const nextMonth = nextMonthDate.getMonth();
    const nextMonthYear = nextMonthDate.getFullYear();

    monthYear.textContent = `${monthNames[month]} ${year}`;

    const isCurrentMonth = (month === currentMonth && year === currentYear);
    nextMonthBtn.disabled = isCurrentMonth;
    nextMonthBtn.classList.toggle("text-gray-300", isCurrentMonth);
    nextMonthBtn.classList.toggle("text-[#1affb2]", !isCurrentMonth);
    nextMonthBtn.classList.toggle("cursor-not-allowed", isCurrentMonth);
    nextMonthBtn.classList.toggle("hover:underline", !isCurrentMonth);

    let day = 1;
    let weekDayIndex = 0;
    let weekRow = null;
    let nextDay = 1;

    // Fetch profits for the current month
    const { month_profits } = await fetchProfits(year, month + 1);

    while (day <= lastDate || weekDayIndex % 7 !== 0) {
        if (weekDayIndex % 7 === 0) {
            if (weekRow) {
                calendarGrid.appendChild(weekRow);
            }
            weekRow = document.createElement("div");
            weekRow.className = "grid grid-cols-8 gap-2 items-stretch";
            var weekProfit = 0;
        }

        let box = document.createElement("div");

        const isBeforeFirst = weekDayIndex < firstDay;
        const isAfterLast = day > lastDate;

        if (isBeforeFirst) {
            const prevDay = prevMonthLastDate - (firstDay - weekDayIndex - 1);
            const savedProfit = (await fetchProfits(prevMonthYear, prevMonth + 1)).month_profits.find(p => p.day === prevDay)?.profit || 0;

            box.className = "calendar-cell inactive flex flex-col justify-start items-center";
            box.innerHTML = `
              <span class="absolute top-1 left-1 text-sm">${prevDay}</span>
              <span class="calendar-profit positive">${savedProfit ? `$${savedProfit}` : ''}</span>
            `;
        } else if (!isAfterLast) {
            const thisDate = new Date(year, month, day);
            const isFuture = thisDate > today;
            const capturedDay = day;

            box.className = "calendar-cell flex flex-col justify-start items-center";
            if (isFuture) {
                box.classList.add("inactive");
            } else {
                box.classList.add("cursor-pointer", "hover:shadow-lg");
                box.addEventListener("click", () => {
                    window.location.href = `/entry?day=${capturedDay}&month=${month + 1}&year=${year}&returnMonth=${month + 1}&returnYear=${year}`;
                });
            }

            // Highlight today
            if (thisDate.toDateString() === today.toDateString()) {
                box.classList.add("selected", "today");
            }

            box.innerHTML = `
              <span class="absolute top-1 left-1 text-sm text-white" style="left: 50%;transform:translateX(-50%);">${capturedDay}</span>
              <span id="profit-${capturedDay}" class="calendar-profit"></span>
            `;

            const savedProfit = month_profits.find(p => p.day === capturedDay)?.profit || 0;
            if (savedProfit) {
                const profitEl = box.querySelector(`#profit-${capturedDay}`);
                profitEl.textContent = `$${savedProfit}`;
                profitEl.classList.add(savedProfit < 0 ? "negative" : "positive");
                weekProfit += savedProfit;
            }

            day++;
        } else {
            const savedProfit = (await fetchProfits(nextMonthYear, nextMonth + 1)).month_profits.find(p => p.day === nextDay)?.profit || 0;

            box.className = "calendar-cell inactive flex flex-col justify-start items-center";
            box.innerHTML = `
              <span class="absolute top-1 left-1 text-sm">${nextDay}</span>
              <span class="calendar-profit positive">${savedProfit ? `$${savedProfit}` : ''}</span>
            `;
            nextDay++;
        }

        weekRow.appendChild(box);
        weekDayIndex++;

        if (weekDayIndex % 7 === 0) {
            const totalBox = document.createElement("div");
            const profitClass = weekProfit >= 0 ? "text-green-600" : "text-red-600";
            totalBox.className = `bg-blue-50 ${profitClass} text-sm font-semibold flex items-center justify-center border rounded-lg h-20 px-2 whitespace-nowrap`;
            totalBox.textContent = `$${weekProfit.toLocaleString()}`;
            weekRow.appendChild(totalBox);
        }
    }

    if (weekRow) {
        calendarGrid.appendChild(weekRow);
    }
}

prevMonthBtn.addEventListener("click", () => {
    viewingDate.setMonth(viewingDate.getMonth() - 1);
    renderCalendar(viewingDate);
});

nextMonthBtn.addEventListener("click", () => {
    const nextMonth = new Date(viewingDate.getFullYear(), viewingDate.getMonth() + 1);
    const isPastToday = nextMonth <= new Date(currentYear, currentMonth, 1);
    if (isPastToday) {
    viewingDate.setMonth(viewingDate.getMonth() + 1);
    renderCalendar(viewingDate);
    }
});

renderCalendar(viewingDate);