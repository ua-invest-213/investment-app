# Import necessary libraries
import yfinance as yf  # For fetching stock data from Yahoo Finance
import openai  # For interacting with the ChatGPT API
import requests  # For making HTTP requests to external APIs
from datetime import datetime  # For working with dates and timestamps
from dotenv import load_dotenv  # For loading environment variables from a .env file
import time  # For adding delays in retry logic
import os  # For accessing environment variables

# Explicitly load the api.env file to access API keys and other sensitive information
load_dotenv("api.env")

# Access the environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()  # OpenAI API key for ChatGPT
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()  # Google Custom Search API key
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID", "").strip()  # Google Custom Search Engine ID

# Set the OpenAI API key for the OpenAI library
openai.api_key = OPENAI_API_KEY

# Function to fetch stock data using Yahoo Finance
def fetch_stock_data(symbol):
    """
    Fetch stock data for a given symbol using Yahoo Finance.

    Args:
        symbol (str): The stock ticker symbol (e.g., "AAPL" for Apple Inc.).

    Returns:
        dict: A dictionary containing stock information such as company name, sector, industry,
              market capitalization, P/E ratio, dividend yield, and the most recent fiscal quarter.
    """
    try:
        # Create a Ticker object for the given stock symbol
        stock = yf.Ticker(symbol)

        # Extract stock information from the Yahoo Finance API
        stock_info = {
            "symbol": symbol,  # Stock ticker symbol
            "long_name": stock.info.get("longName", "N/A"),  # Full company name
            "sector": stock.info.get("sector", "N/A"),  # Sector (e.g., "Technology")
            "industry": stock.info.get("industry", "N/A"),  # Industry (e.g., "Software")
            "market_cap": stock.info.get("marketCap", "N/A"),  # Market capitalization
            "pe_ratio": stock.info.get("trailingPE", "N/A"),  # Price-to-earnings ratio
            "dividend_yield": stock.info.get("dividendYield", "N/A"),  # Dividend yield
            "current_price": stock.info.get("currentPrice", "N/A"),  # Current stock price
        }

        # Attempt to fetch the last fiscal quarter from Yahoo Finance
        recent_quarter = stock.info.get("lastFiscalQuarterEnd", None)

        if recent_quarter:
            # Convert the fiscal quarter date to a readable format
            stock_info["recent_quarter"] = datetime.strptime(recent_quarter, "%Y-%m-%d").strftime("%Y-%m-%d")
        else:
            # Dynamically calculate the most recent fiscal quarter if unavailable
            today = datetime.now()
            if today.month in [1, 2, 3]:
                recent_quarter = f"{today.year - 1}-12-31"
            elif today.month in [4, 5, 6]:
                recent_quarter = f"{today.year}-03-31"
            elif today.month in [7, 8, 9]:
                recent_quarter = f"{today.year}-06-30"
            else:
                recent_quarter = f"{today.year}-09-30"

            stock_info["recent_quarter"] = recent_quarter

        return stock_info  # Return the stock information as a dictionary
    except Exception as e:
        # Handle any errors that occur during the API call
        print(f"Error fetching data for {symbol}: {e}")
        return None

# Function to scrape company data using Google Custom Search API
def scrape_company_data(symbol):
    """
    Use Google Custom Search API to fetch company data from the web.

    Args:
        symbol (str): The stock ticker symbol (e.g., "AAPL" for Apple Inc.).

    Returns:
        dict: A dictionary containing the title, snippet, and link of the first search result.
    """
    try:
        # Ensure API key and search engine ID are set
        if not GOOGLE_API_KEY or not SEARCH_ENGINE_ID:
            raise ValueError("GOOGLE_API_KEY or SEARCH_ENGINE_ID is not set.")

        # Construct the search query to fetch company profile information
        query = f"{symbol} company profile -site:finance.yahoo.com"
        url = f"https://www.googleapis.com/customsearch/v1"
        params = {
            "key": GOOGLE_API_KEY,  # Google API key
            "cx": SEARCH_ENGINE_ID,  # Custom search engine ID
            "q": query,  # Search query
        }

        # Make the API request to Google Custom Search
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an error for bad status codes
        search_results = response.json()  # Parse the JSON response

        # Extract relevant data from the search results
        if "items" in search_results:
            first_result = search_results["items"][0]  # Get the first search result
            title = first_result.get("title", "N/A")  # Title of the result
            snippet = first_result.get("snippet", "N/A")  # Short description of the result
            link = first_result.get("link", "N/A")  # URL of the result

            return {
                "title": title,
                "snippet": snippet,
                "link": link,
            }
        else:
            return None  # No search results found
    except ValueError as ve:
        # Handle configuration errors (e.g., missing API keys)
        print(f"Configuration Error: {ve}")
        return None
    except requests.exceptions.RequestException as e:
        # Handle errors related to the HTTP request
        print(f"Error fetching data from Google Custom Search API: {e}")
        return None

# Function to get a synopsis using ChatGPT
def get_company_synopsis(long_name, recent_quarter, pe_ratio, scraped_data):
    """
    Use ChatGPT API to generate a short synopsis of the company's history,
    its most recent fiscal quarter, and provide a recommendation based on the P/E ratio.

    Args:
        long_name (str): The full name of the company.
        recent_quarter (str): The most recent fiscal quarter.
        pe_ratio (float): The price-to-earnings ratio of the company.
        scraped_data (dict): Data scraped from Google Custom Search API.

    Returns:
        str: A synopsis of the company.
    """
    try:
        # Determine the recommendation based on the P/E ratio
        if pe_ratio is None or pe_ratio == "N/A":
            recommendation = "No recommendation (P/E ratio unavailable)."
        elif pe_ratio < 15:
            recommendation = "Buy"
        elif 15 <= pe_ratio <= 25:
            recommendation = "Hold"
        else:
            recommendation = "Sell"

        # Extract relevant web-scraped data
        title = scraped_data.get("title", "N/A") if scraped_data else "N/A"
        snippet = scraped_data.get("snippet", "N/A") if scraped_data else "N/A"

        # Construct a concise prompt for ChatGPT
        prompt = (
            f"Summarize the company '{long_name}' (stock ticker: {title}), "
            f"its most recent fiscal quarter ending on {recent_quarter}, "
            f"and provide a recommendation based on its P/E ratio of {pe_ratio}. "
            f"The recommendation is: {recommendation}. "
            f"Additional context: {snippet}."
        )

        # Retry logic for ChatGPT API
        retries = 3
        for attempt in range(retries):
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a highly skilled financial analyst."},
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=200,  # Limit response length
                    temperature=0.7,  # Control randomness
                )
                return response["choices"][0]["message"]["content"]
            except Exception as e:
                time.sleep(5)  # Wait 5 seconds before retrying

        raise Exception("Failed to connect to OpenAI API after multiple retries.")
    except Exception as e:
        # Handle errors during the ChatGPT API call
        print(f"Error fetching company synopsis: {e}")
        return "Unable to fetch company synopsis."

# Function to analyze stock data
def analyze_stock_data(stock_data):
    """
    Analyze stock data and provide a Buy, Sell, or Hold recommendation.

    Args:
        stock_data (dict): A dictionary containing stock information.

    Returns:
        str: A recommendation ("Buy", "Sell", "Hold", or "No Rating").
    """
    try:
        # Extract the P/E ratio from the stock data
        pe_ratio = stock_data.get("pe_ratio", None)
        if pe_ratio is None or pe_ratio == "N/A":
            return "No Rating (P/E ratio unavailable)"
        elif pe_ratio < 15:
            return "Buy"
        elif 15 <= pe_ratio <= 25:
            return "Hold"
        else:
            return "Sell"
    except Exception as e:
        # Handle errors during analysis
        print(f"Error analyzing stock data: {e}")
        return "Unable to provide a rating."

# Main function
def main():
    """
    Main program execution.
    """
    # Get user input for stock symbol
    symbol = input("Enter the stock symbol: ").upper()

    # Open a text file to write the output
    output_file = f"{symbol}_analysis.txt"
    with open(output_file, "w") as file:
        # Fetch stock data using Yahoo Finance
        stock_data = fetch_stock_data(symbol)
        if stock_data:
            # Write stock information to the file
            file.write("=== Stock Information ===\n")
            for key, value in stock_data.items():
                file.write(f"{key.capitalize()}: {value}\n")
            file.write("\n")

            # Analyze stock data to determine Buy, Sell, or Hold
            rating = analyze_stock_data(stock_data)
            file.write("=== Rating ===\n")
            file.write(f"The rating for {symbol} is: {rating}\n\n")
        else:
            # Write error message to the file
            file.write("Unable to fetch stock data.\n")
            return

        # Scrape company data using Google Custom Search API
        scraped_data = scrape_company_data(symbol)
        if scraped_data:
            # Get company synopsis
            synopsis = get_company_synopsis(
                stock_data["long_name"],
                stock_data.get("recent_quarter", "N/A"),
                stock_data.get("pe_ratio", "N/A"),
                scraped_data
            )
            file.write("=== Company Synopsis ===\n")
            file.write(synopsis + "\n")
        else:
            # Write error message to the file
            file.write("Unable to fetch company data.\n")
            return

    # Notify the user that the text file is ready
    print(f"Analysis for {symbol} has been saved to {output_file}. You can now open and read the file.")

# Entry point
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")