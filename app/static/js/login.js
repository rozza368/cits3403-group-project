function togglePassword() {
    const pwd = document.getElementById('password');
    const icon = document.getElementById('eyeIcon');
    if (pwd.type === 'password') {
    pwd.type = 'text';
    icon.innerHTML = `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
        d="M13.875 18.825A10.05 10.05 0 0112 19c-4.418 0-8-3.134-8-7a9.978 9.978 0 013.563-7.563M15 12a3 3 0 11-6 0 3 3 0 016 0zm6 0c0 1.657-.672 3.157-1.757 4.243M3 3l18 18" />`;
    } else {
    pwd.type = 'password';
    icon.innerHTML = `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
        d="M15 12a3 3 0 11-6 0 3 3 0 016 0zm6 0c0 3.866-3.582-7-8-7s-8-3.134-8-7 3.582-7 8-7 8 3.134 8 7z" />`;
    }
}

// Fetch crypto prices (using CoinGecko API)
async function fetchCryptoPrices() {
    try {
    const res = await fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,binancecoin,cardano,dogecoin&vs_currencies=usd');
    if (!res.ok) throw new Error('Price fetch failed');
    const data = await res.json();
    const prices = [
        { name: 'Bitcoin', id: 'bitcoin' },
        { name: 'Ethereum', id: 'ethereum' },
        { name: 'Solana', id: 'solana' },
        { name: 'BNB', id: 'binancecoin' },
        { name: 'Cardano', id: 'cardano' },
        { name: 'Dogecoin', id: 'dogecoin' }
    ];
    const pricesContainer = document.getElementById('cryptoPrices');
    pricesContainer.innerHTML = '';
    prices.forEach(coin => {
        pricesContainer.innerHTML += `
        <div class="flex flex-col items-center min-w-[100px]">
            <span class="font-semibold">${coin.name}</span>
            <span class="text-gray-700 text-lg">$${data[coin.id].usd.toLocaleString()}</span>
        </div>
        `;
    });
    } catch (e) {
    document.getElementById('cryptoPrices').innerHTML = '<div class="text-red-500">Unable to load prices at this time.</div>';
    }
}
fetchCryptoPrices();
setInterval(fetchCryptoPrices, 60000);

// Fetch latest crypto news from your Flask backend
async function fetchCryptoNews() {
    try {
    const res = await fetch('/api/cryptonews');
    if (!res.ok) throw new Error('News fetch failed');
    const news = await res.json();
    const newsContainer = document.getElementById('cryptoNews');
    newsContainer.innerHTML = '';
    news.forEach(article => {
        newsContainer.innerHTML += `
        <a href="${article.url}" target="_blank" class="block bg-white rounded-lg shadow hover:shadow-lg transition p-4">
            <div class="font-semibold text-lg mb-2">${article.title}</div>
            <div class="text-gray-500 text-sm mb-1">${article.published_on ? new Date(article.published_on * 1000).toLocaleDateString() : ''}</div>
            <div class="text-gray-700 text-sm">${article.source || ''}</div>
        </a>
        `;
    });
    } catch (e) {
    document.getElementById('cryptoNews').innerHTML = '<div class="text-red-500">Unable to load news at this time.</div>';
    }
}
fetchCryptoNews();
setInterval(fetchCryptoNews, 1000 * 60 * 60 * 2);
