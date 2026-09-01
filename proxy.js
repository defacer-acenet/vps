const axios = require('axios');
const fs = require('fs');

async function scrapeProxies() {
  const proxySources = [
    // HTTP
    { type: 'http', url: 'https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&protocol=http&proxy_format=ipport&format=text&timeout=20000' },
    { type: 'http', url: 'https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/http.txt' },
    { type: 'https', url: 'https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/https.txt' },
    { type: 'http', url: 'https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/http.txt' },
    { type: 'https', url: 'https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/https.txt' },
    { type: 'http', url: 'https://raw.githubusercontent.com/BreakingTechFr/Proxy_Free/main/proxies/http.txt' },
    { type: 'http', url: 'https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt' },
    { type: 'http', url: 'https://raw.githubusercontent.com/monosans/proxy-list/main/proxies_anonymous/http.txt' },
    { type: 'http', url: 'https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/http/http.txt' },
    { type: 'http', url: 'https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/http.txt' },
    { type: 'https', url: 'https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/https.txt' },
    { type: 'http', url: 'https://raw.githubusercontent.com/berkay-digital/Proxy-Scraper/main/proxies.txt' },
    { type: 'http', url: 'https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt' },
    { type: 'http', url: 'https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt' },
    { type: 'https', url: 'https://raw.githubusercontent.com/mmpx12/proxy-list/master/https.txt' },
    { type: 'http', url: 'https://raw.githubusercontent.com/ALIILAPRO/Proxy/main/http.txt' },
    { type: 'http', url: 'https://raw.githubusercontent.com/HumayunShariarHimu/Proxy/main/Anonymous_HTTP_One.md' },
    { type: 'https', url: 'https://raw.githubusercontent.com/ArrayIterator/proxy-lists/main/proxies/https.txt' },
    { type: 'http', url: 'https://raw.githubusercontent.com/ArrayIterator/proxy-lists/main/proxies/http.txt' },
    { type: 'http', url: 'https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt' },
    { type: 'http', url: 'https://raw.githubusercontent.com/zloi-user/hideip.me/main/http.txt' },
    { type: 'https', url: 'https://raw.githubusercontent.com/zloi-user/hideip.me/main/https.txt' },
    { type: 'http', url: 'https://raw.githubusercontent.com/elliottophellia/proxylist/master/results/http/global/http_checked.txt' },
    { type: 'https', url: 'https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/https/https.txt' },
    { type: 'http', url: 'https://raw.githubusercontent.com/Vann-Dev/proxy-list/main/proxies/http.txt' },
    { type: 'https', url: 'https://raw.githubusercontent.com/ObcbO/getproxy/master/file/https.txt' },
    { type: 'http', url: 'https://raw.githubusercontent.com/ObcbO/getproxy/master/file/http.txt' },
    { type: 'https', url: 'https://raw.githubusercontent.com/Vann-Dev/proxy-list/main/proxies/https.txt' },
    { type: 'http', url: 'https://raw.githubusercontent.com/themiralay/Proxy-List-World/master/data.txt' },
    { type: 'http', url: 'https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt' },
    { type: 'http', url: 'https://raw.githubusercontent.com/Skiddle-ID/proxylist/main/proxies.txt' },
    { type: 'http', url: 'https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/main/proxy_files/http_proxies.txt' },
    { type: 'https', url: 'https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/main/proxy_files/https_proxies.txt' },
    { type: 'http', url: 'https://raw.githubusercontent.com/MrMarble/proxy-list/main/all.txt' },
    { type: 'http', url: 'https://raw.githubusercontent.com/ProxyScraper/ProxyScraper/main/http.txt' },
    { type: 'http', url: 'https://raw.githubusercontent.com/TuanMinPay/live-proxy/master/http.txt' },
    { type: 'https', url: 'https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt' },
    { type: 'http', url: 'https://raw.githubusercontent.com/zevtyardt/proxy-list/main/http.txt' },
    { type: 'http', url: 'https://raw.githubusercontent.com/miyukii-chan/proxy-list/master/proxies/http.txt' },
    { type: 'http', url: 'https://raw.githubusercontent.com/mertguvencli/http-proxy-list/main/proxy-list/data.txt' },
    { type: 'https', url: 'https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-https.txt' },
    { type: 'http', url: 'https://raw.githubusercontent.com/j0rd1s3rr4n0/api/main/proxy/http.txt' },
    { type: 'https', url: 'https://raw.githubusercontent.com/HyperBeats/proxy-list/main/https.txt' },
    { type: 'http', url: 'https://raw.githubusercontent.com/HyperBeats/proxy-list/main/http.txt' },

    // SOCKS
    { type: 'socks5', url: 'https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt' },
    { type: 'socks4', url: 'https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks4.txt' },
    { type: 'http', url: 'https://proxyspace.pro/http.txt' },
    { type: 'socks5', url: 'https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt' },
    { type: 'socks4', url: 'https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/socks4.txt' },
    { type: 'socks5', url: 'https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/socks5.txt' },
    { type: 'http', url: 'https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/http.txt' },
    { type: 'socks4', url: 'https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/socks4.txt' },
    { type: 'socks5', url: 'https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/socks5.txt' },
    { type: 'socks4', url: 'https://raw.githubusercontent.com/zloi-user/hideip.me/main/socks4.txt' },
    { type: 'socks5', url: 'https://raw.githubusercontent.com/zloi-user/hideip.me/main/socks5.txt' },
    { type: 'socks4', url: 'https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/socks4/socks4.txt' },
    { type: 'socks5', url: 'https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/socks5/socks5.txt' },
    { type: 'socks4', url: 'https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/main/proxy_files/socks4_proxies.txt' },
    { type: 'socks5', url: 'https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/main/proxy_files/socks5_proxies.txt' },
    { type: 'socks5', url: 'https://raw.githubusercontent.com/ObcbO/getproxy/master/file/socks5.txt' },
    { type: 'socks4', url: 'https://raw.githubusercontent.com/ObcbO/getproxy/master/file/socks4.txt' },
  ];

  let proxies = [];

  // Remove old proxy file
  if (fs.existsSync('proxy.txt')) {
    fs.unlinkSync('proxy.txt');
    console.log('Old proxy file successfully deleted');
  }

  // Scrape each source
  for (const source of proxySources) {
    try {
      const response = await axios.get(source.url, {
        timeout: 10000,
        responseType: 'text'
      });

      const newProxies = String(response.data)
        .split(/\r?\n/)
        .map(proxy => proxy.trim())
        .filter(Boolean)
        .map(proxy => `(${source.type})${proxy}`);

      proxies.push(...newProxies);

      console.log(
        `Success: ${newProxies.length} proxies | (${source.type}) ${source.url}`
      );
    } catch (error) {
      console.log(`Failed: (${source.type}) ${source.url}`);
      console.log(
        error.response?.status ||
        error.code ||
        error.message
      );
    }
  }

  // Remove duplicate proxies
  proxies = [...new Set(proxies)];

  // Save proxies to file
  fs.writeFileSync(
    'proxy.txt',
    proxies.join('\n'),
    'utf8'
  );

  console.log('');
  console.log('======================================');
  console.log('Proxies successfully scraped');
  console.log(`Total proxies: ${proxies.length}`);
  console.log('Saved to: proxy.txt');
  console.log('======================================');
}

module.exports = scrapeProxies;

// Run the scraper
scrapeProxies().catch(error => {
  console.error('Fatal error:', error.message);
});
