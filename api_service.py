import requests
import logging
import os
import time
import html
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

class CryptoAPIService:
    def __init__(self):
        self.coingecko_base_url = "https://api.coingecko.com/api/v3"
        self.opensea_base_url = "https://api.opensea.io/api/v2"
        self.cryptopanic_base_url = "https://cryptopanic.com/api/v1"
        self.cryptopanic_api_key = os.getenv("CRYPTOPANIC_API_KEY", "")
        self.opensea_api_key = os.getenv("OPENSEA_API_KEY", "")
        self.fear_greed_url = "https://api.alternative.me/fng"

        # ----- Cache for charts and converter -----
        self._cache = {}
        self._cache_expiry = 300  # 5 minutes

    # ----------- Internal Request with Retry -----------
    def _safe_request(self, url: str, params: dict = None, headers: dict = None, max_retries: int = 3) -> Optional[dict]:
        for attempt in range(max_retries):
            try:
                response = requests.get(url, params=params, headers=headers, timeout=10)
                if response.status_code == 429:
                    wait = 2 * (attempt + 1)
                    logger.warning(f"Rate limited (429). Retrying in {wait}s...")
                    time.sleep(wait)
                    continue
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")
                time.sleep(1)
        return {}

    # ----------- Cache Helpers -----------
    def _get_cache(self, key):
        entry = self._cache.get(key)
        if entry and time.time() - entry['time'] < self._cache_expiry:
            return entry['data']
        return None

    def _set_cache(self, key, data):
        self._cache[key] = {'data': data, 'time': time.time()}

    # ----------- CoinGecko Methods -----------
    def get_trending_coins(self) -> List[Dict]:
        cache_key = "trending_coins"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        data = self._safe_request(f"{self.coingecko_base_url}/search/trending")
        coins = data.get('coins', [])
        self._set_cache(cache_key, coins)
        return coins

    def get_coin_prices(self, coin_ids: List[str], vs_currency: str = 'usd') -> Dict:
        cache_key = f"coin_prices_{'_'.join(coin_ids)}_{vs_currency}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        ids_str = ','.join(coin_ids)
        params = {
            'ids': ids_str,
            'vs_currencies': vs_currency,
            'include_24hr_change': 'true',
            'include_market_cap': 'true',
            'include_24hr_vol': 'true'
        }
        data = self._safe_request(f"{self.coingecko_base_url}/simple/price", params=params) or {}
        self._set_cache(cache_key, data)
        return data

    def get_top_coins(self, limit: int = 100, page: int = 1) -> List[Dict]:
        cache_key = f"top_coins_{limit}_{page}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        params = {
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': limit,
            'page': page,
            'sparkline': 'false',
            'price_change_percentage': '24h,7d'
        }
        data = self._safe_request(f"{self.coingecko_base_url}/coins/markets", params=params) or []
        self._set_cache(cache_key, data)
        return data

    def search_coins(self, query: str) -> Dict:
        cache_key = f"search_coins_{query}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        data = self._safe_request(f"{self.coingecko_base_url}/search", params={'query': query}) or {}
        self._set_cache(cache_key, data)
        return data

    # ----------- Charts (Coin History) using CryptoCompare -----------
    def get_coin_history(self, coin_symbol: str, days: int = 30) -> Dict:
        cache_key = f"history_{coin_symbol}_{days}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        url = "https://min-api.cryptocompare.com/data/v2/histoday"
        params = {"fsym": coin_symbol.upper(), "tsym": "USD", "limit": days}
        data = self._safe_request(url, params=params) or {}

        prices, market_caps, total_volumes = [], [], []
        try:
            for item in data.get("Data", {}).get("Data", []):
                ts = item.get("time", 0) * 1000
                prices.append([ts, item.get("close", 0)])
                market_caps.append([ts, item.get("volumefrom", 0) * item.get("close", 0)])
                total_volumes.append([ts, item.get("volumeto", 0)])
            if not prices:
                logger.warning(f"No historical data found for {coin_symbol}")
        except Exception as e:
            logger.error(f"Error processing historical data for {coin_symbol}: {e}")

        result = {"prices": prices, "market_caps": market_caps, "total_volumes": total_volumes}
        self._set_cache(cache_key, result)
        return result

    # ----------- Converter (Exchange Rates) using ExchangeRate Host -----------
    def get_exchange_rates(self) -> Dict:
        cache_key = "exchange_rates"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        crypto_prices = self.get_coin_prices(["bitcoin", "ethereum", "binancecoin", "cardano", "solana"], "usd")

        fiat_data = self._safe_request("https://api.exchangerate.host/latest?base=USD") or {}
        rates = fiat_data.get("rates", {})

        result = {}
        for coin in ["bitcoin", "ethereum", "binancecoin", "cardano", "solana"]:
            usd = crypto_prices.get(coin, {}).get("usd")
            if usd is None:
                logger.warning(f"Unable to get USD price for {coin}")
                continue
            result[coin] = {
                "usd": usd,
                "eur": round(usd * rates.get("EUR", 1), 4),
                "gbp": round(usd * rates.get("GBP", 1), 4),
                "jpy": round(usd * rates.get("JPY", 1), 2),
            }

        self._set_cache(cache_key, result)
        return result

    # ----------- Other Methods (unchanged) -----------
    def get_nfts_by_wallet(self, wallet_address: str, chain: str = "ethereum") -> List[Dict]:
        if not self.opensea_api_key:
            logger.warning("OpenSea API key missing. Set OPENSEA_API_KEY.")
            return []
        url = f"{self.opensea_base_url}/chain/{chain}/account/{wallet_address}/nfts"
        headers = {"Accept": "application/json", "X-API-KEY": self.opensea_api_key}
        data = self._safe_request(url, headers=headers)
        return data.get("nfts", [])

    def get_cryptopanic_news(self, filter: str = "news", currencies: str = "BTC") -> List[Dict]:
        if not self.cryptopanic_api_key:
            logger.warning("CryptoPanic API key missing. Set CRYPTOPANIC_API_KEY.")
            return []
        params = {"auth_token": self.cryptopanic_api_key, "filter": filter, "currencies": currencies}
        data = self._safe_request(f"{self.cryptopanic_base_url}/posts/", params=params)
        return data.get("results", [])

    def get_crypto_news(self, limit: int = 20) -> List[Dict]:
        cache_key = f"crypto_news_{limit}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        rss_urls = [
            'https://feeds.feedburner.com/coindesk/CoinDesk',
            'https://cointelegraph.com/rss',
            'https://decrypt.co/feed'
        ]
        all_articles = []

        for rss_url in rss_urls:
            try:
                resp = requests.get(rss_url, timeout=5)
                if resp.status_code != 200:
                    continue
                root = ET.fromstring(resp.content)
                for item in root.findall('.//item')[: limit // len(rss_urls)]:
                    title = item.find('title')
                    link = item.find('link')
                    description = item.find('description')
                    pub_date = item.find('pubDate')
                    article = {
                        'title': html.unescape(title.text.strip()) if title is not None else 'No title',
                        'url': link.text.strip() if link is not None else '',
                        'description': html.unescape(description.text.strip()) if description is not None else '',
                        'published_at': pub_date.text.strip() if pub_date is not None else '',
                        'domain': rss_url.split('/')[2]
                    }
                    all_articles.append(article)
            except Exception as e:
                logger.warning(f"Error parsing RSS {rss_url}: {e}")
        self._set_cache(cache_key, all_articles)
        return all_articles[:limit]

    def get_fear_greed_index(self) -> Dict:
        cache_key = "fear_greed"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        data = self._safe_request(self.fear_greed_url)
        result = data.get('data', [{}])[0] if data.get('data') else {}
        self._set_cache(cache_key, result)
        return result

# Global instance
crypto_api = CryptoAPIService()
