import requests
import os
from dotenv import load_dotenv
from functools import wraps
import functools
import json
from datetime import datetime, timedelta

from logger import setup_logger

load_dotenv()

logger = setup_logger(log_file='logs/info_fetch.log')


def log_and_handle_errors(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            logger.info(f"Calling {func.__name__}")
            result = func(*args, **kwargs)
            logger.info(f"Successfully executed {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            return None
    return wrapper

def dump_output_to_file(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        
        # Create a 'function_outputs' directory if it doesn't exist
        output_dir = 'function_outputs'
        os.makedirs(output_dir, exist_ok=True)
        
        # Create a filename based on the function name
        filename = os.path.join(output_dir, f"{func.__name__}_output.json")
        
        # Write the output to the file
        with open(filename, 'w') as f:
            if isinstance(result, (dict, list)):
                # If the result is a dict or list, dump it as JSON for better readability
                json.dump(result, f, indent=2)
            else:
                # Otherwise, just write it as a string
                f.write(str(result))
        
        return result
    return wrapper


class PolygonAPI:
    def __init__(self):
        self.base_url = "https://api.polygon.io"
        self.api_key = os.getenv("POLYGON_API_KEY")
        if not self.api_key:
            raise ValueError("POLYGON_API_KEY not found in environment variables")

    def _make_request(self, endpoint, params=None):
        url = f"{self.base_url}{endpoint}"
        params = params or {}
        params['apiKey'] = self.api_key
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"An error occurred: {e}")
            return None

class AggregatesData:
    def __init__(self, polygon_api):
        self.polygon_api = polygon_api

    @log_and_handle_errors
    def get_aggregates(self, ticker, multiplier, timespan, from_date, to_date):
        endpoint = f"/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from_date}/{to_date}"
        return self.polygon_api._make_request(endpoint)

class DailyOpenClose:
    def __init__(self, polygon_api):
        self.polygon_api = polygon_api

    @log_and_handle_errors
    def get_daily_open_close(self, ticker, date):
        endpoint = f"/v1/open-close/{ticker}/{date}"
        return self.polygon_api._make_request(endpoint)


class TickerDetails:
    def __init__(self, polygon_api):
        self.polygon_api = polygon_api

    @log_and_handle_errors
    def get_ticker_details(self, ticker):
        endpoint = f"/v3/reference/tickers/{ticker}"
        return self.polygon_api._make_request(endpoint)

    @log_and_handle_errors
    def get_cik(self, ticker):
        details = self.get_ticker_details(ticker)
        return details['results']['cik']

class TickerNews:
    def __init__(self, polygon_api):
        self.polygon_api = polygon_api

    @log_and_handle_errors
    def get_ticker_news(self, ticker, limit=10):
        endpoint = "/v2/reference/news"
        params = {'ticker': ticker, 'limit': limit}
        return self.polygon_api._make_request(endpoint, params)

class StockSplits:
    def __init__(self, polygon_api):
        self.polygon_api = polygon_api

    @log_and_handle_errors
    def get_stock_splits(self, ticker):
        endpoint = "/v3/reference/splits"
        params = {'ticker': ticker}
        return self.polygon_api._make_request(endpoint, params)

class Dividends:
    def __init__(self, polygon_api):
        self.polygon_api = polygon_api

    @log_and_handle_errors
    def get_dividends(self, ticker):
        endpoint = "/v3/reference/dividends"
        params = {'ticker': ticker}
        return self.polygon_api._make_request(endpoint, params)

class StockFinancials:
    def __init__(self, polygon_api):
        self.polygon_api = polygon_api

    @log_and_handle_errors
    def get_financials(self, ticker, limit=5):
        endpoint = "/vX/reference/financials"
        params = {'ticker': ticker, 'limit': limit}
        return self.polygon_api._make_request(endpoint, params)

class TechnicalIndicators:
    def __init__(self, polygon_api):
        self.polygon_api = polygon_api

    @log_and_handle_errors
    def get_sma(self, ticker, timespan, window, series_type='close'):
        endpoint = f"/v1/indicators/sma/{ticker}"
        params = {
            'timespan': timespan,
            'window': window,
            'series_type': series_type
        }
        return self.polygon_api._make_request(endpoint, params)

class MarketStatus:
    def __init__(self, polygon_api):
        self.polygon_api = polygon_api

    @log_and_handle_errors
    def get_market_status(self):
        endpoint = "/v1/marketstatus/now"
        return self.polygon_api._make_request(endpoint)
    
class SECEdgarSearch:
    def __init__(self, cik):
        self.base_url = "https://data.sec.gov"
        self.cik = cik
        self.headers = {
            "User-Agent": "Anandkumar NS StockAnalyzer/1.0 anandkumarns@gmail.com"  
        }

    @log_and_handle_errors
    def get_company_facts(self):
        url = f"{self.base_url}/api/xbrl/companyfacts/CIK{self.cik.zfill(10)}.json"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"An error occurred while fetching company facts: {e}")
            return None

    @log_and_handle_errors
    def get_company_filings(self):
        url = f"{self.base_url}/submissions/CIK{self.cik.zfill(10)}.json"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"An error occurred while fetching company filings: {e}")
            return None
    
    @log_and_handle_errors
    def sec_search(self):
        return {
            "company_facts": self.get_company_facts(),
            "company_filings": self.get_company_filings()
        }

class StockAnalyzer:
    def __init__(self):
        self.polygon_api = PolygonAPI()
        self.aggregates = AggregatesData(self.polygon_api)
        self.daily_open_close = DailyOpenClose(self.polygon_api)
        self.ticker_details = TickerDetails(self.polygon_api)
        self.ticker_news = TickerNews(self.polygon_api)
        self.stock_splits = StockSplits(self.polygon_api)
        self.dividends = Dividends(self.polygon_api)
        self.financials = StockFinancials(self.polygon_api)
        self.technical_indicators = TechnicalIndicators(self.polygon_api)
        self.market_status = MarketStatus(self.polygon_api)
    
    @log_and_handle_errors
    def get_latest_trading_day(self):
        today = datetime.now()
        if today.weekday() >= 5:  # Saturday or Sunday
            latest_trading_day = today - timedelta(days=today.weekday() - 4)
        else:
            latest_trading_day = today - timedelta(days=1)
        return latest_trading_day.strftime("%Y-%m-%d")

    @log_and_handle_errors
    # @dump_output_to_file
    def analyze_stock(self, ticker):
        latest_trading_day = self.get_latest_trading_day()
        details = self.ticker_details.get_ticker_details(ticker)
        recent_aggs = self.aggregates.get_aggregates(
            ticker, 1, "day", 
            (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"), 
            latest_trading_day
        )
        open_close = self.daily_open_close.get_daily_open_close(ticker, latest_trading_day)
        dividends = self.dividends.get_dividends(ticker)
        splits = self.stock_splits.get_stock_splits(ticker)
        technicalIndicators = self.technical_indicators.get_sma(ticker, "day", 50)
        news = self.ticker_news.get_ticker_news(ticker)
        cik = self.ticker_details.get_cik(ticker)
        financials = self.financials.get_financials(ticker)
        sma_50 = self.technical_indicators.get_sma(ticker, "day", 50)
        self.sec_edgar_search = SECEdgarSearch(cik)
        sec_edgar_filings = self.sec_edgar_search.sec_search()

        if cik:
            self.sec_edgar_search = SECEdgarSearch(cik)
            sec_edgar_filings = self.sec_edgar_search.sec_search()
        else:
            print(f"Failed to fetch CIK for {ticker}")
            sec_edgar_filings = None

        # You would process and combine this data to create your analysis
        # For now, we'll just return a dictionary of the raw data
        return {
            "details": details['results'],
            "recent_aggregates": recent_aggs['results'],
            "news": news['results'],
            "financials": financials['results'],
            "sma_50": sma_50['results'],
            "open_close": open_close,
            "dividends": dividends['results'],
            "splits": splits['results'],
            "technical_indicators": technicalIndicators['results'],
            "sec_edgar_filings": sec_edgar_filings

        }

# Usage
if __name__ == "__main__":
    analyzer = StockAnalyzer()
    analysis = analyzer.analyze_stock("AAPL")
    print(analysis)