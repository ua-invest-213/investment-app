# stock_analysis.py
import requests
from datetime import datetime
from stockthing.v2.pythonversion.utils import rate_limit_check, log_error

def fetch_stock_data(symbol, api_key):
    """
    Fetch stock data for a given symbol using the Alpha Vantage API.
    """
    try:
        # Check and handle rate limits before making the API call
        rate_limit_check()

        # Fetch company overview data from Alpha Vantage
        overview_url = "https://www.alphavantage.co/query"
        overview_params = {
            "function": "OVERVIEW",
            "symbol": symbol,
            "apikey": api_key,  # Use the provided API key
        }
        overview_response = requests.get(overview_url, params=overview_params)
        overview_data = overview_response.json()

        # If the response does not contain the "Symbol" key, raise an error
        if "Symbol" not in overview_data:
            raise ValueError(f"Unable to fetch data for symbol: {symbol}. Response: {overview_data}")

        # Fetch earnings data from Alpha Vantage
        rate_limit_check()
        earnings_url = "https://www.alphavantage.co/query"
        earnings_params = {
            "function": "EARNINGS",
            "symbol": symbol,
            "apikey": api_key,  # Use the provided API key
        }
        earnings_response = requests.get(earnings_url, params=earnings_params)
        earnings_data = earnings_response.json()

        # Extract the most recent fiscal quarter from the earnings data
        recent_quarter = "N/A"
        if "quarterlyEarnings" in earnings_data:
            recent_quarter = earnings_data["quarterlyEarnings"][0]["fiscalDateEnding"]

        # Build a dictionary containing the stock information
        stock_info = {
            "symbol": symbol,
            "long_name": overview_data.get("Name", "N/A"),
            "sector": overview_data.get("Sector", "N/A"),
            "industry": overview_data.get("Industry", "N/A"),
            "market_cap": overview_data.get("MarketCapitalization", "N/A"),
            "pe_ratio": overview_data.get("PERatio", "N/A"),
            "dividend_yield": overview_data.get("DividendYield", "N/A"),
            "current_price": overview_data.get("50DayMovingAverage", "N/A"),
            "recent_quarter": recent_quarter,
        }

        return stock_info
    except Exception as e:
        log_error(f"Error fetching data for {symbol}: {e}")
        return None

def analyze_stock_data(stock_data):
    """
    Analyze stock data and provide a Buy, Sell, or Hold recommendation.
    """
    try:
        pe_ratio = stock_data.get("pe_ratio", None)
        if pe_ratio is None or pe_ratio == "N/A":
            return "No Rating (P/E ratio unavailable)"
        elif float(pe_ratio) < 15:
            return "Buy"
        elif 15 <= float(pe_ratio) <= 25:
            return "Hold"
        else:
            return "Sell"
    except Exception as e:
        log_error(f"Error analyzing stock data: {e}")
        return "Unable to provide a rating."