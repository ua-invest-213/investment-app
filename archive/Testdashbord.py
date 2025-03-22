# Import necessary libraries
import openai  # For OpenAI API integration (currently unused in this script)
import requests  # For making HTTP requests to the Alpha Vantage API
from datetime import datetime  # For handling timestamps and logging
from dotenv import load_dotenv, find_dotenv  # For loading environment variables from a .env file
import os  # For interacting with the operating system (e.g., reading environment variables)
import time  # For handling rate-limiting and delays
import streamlit as st  # For creating an interactive dashboard

# Load the .env file to access API keys
dotenv_path = find_dotenv("api.env")
if dotenv_path:
    load_dotenv(dotenv_path)

# Access the environment variables for API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()  # OpenAI API key (not used in this script)
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "").strip()  # Alpha Vantage API key

# Set the OpenAI API key (not used in this script)
openai.api_key = OPENAI_API_KEY

# Global variables to track API calls and rate-limiting
api_call_count = 0  # Tracks the number of API calls made in the current minute
start_time = time.time()  # Tracks the start time of the current minute

def rate_limit_check():
    """
    Check if the API call limit has been reached and wait if necessary.
    Alpha Vantage's free tier allows 5 API calls per minute.
    This function ensures the program respects that limit.
    """
    global api_call_count, start_time

    # Calculate the elapsed time since the start of the current minute
    elapsed_time = time.time() - start_time

    # If more than a minute has passed, reset the counter and start time
    if elapsed_time > 60:
        api_call_count = 0
        start_time = time.time()

    # If the API call limit is reached, wait for the remaining time in the minute
    if api_call_count >= 5:
        wait_time = 60 - elapsed_time
        print(f"Rate limit reached. Waiting for {wait_time:.2f} seconds...")
        time.sleep(wait_time)  # Pause execution until the limit resets
        api_call_count = 0  # Reset the counter after waiting
        start_time = time.time()  # Reset the start time

    # Increment the API call count for each request
    api_call_count += 1
    print(f"API call #{api_call_count} made.")

def fetch_stock_data(symbol):
    """
    Fetch stock data for a given symbol using the Alpha Vantage API.
    This function retrieves both company overview and earnings data.

    Args:
        symbol (str): The stock symbol (e.g., "TSLA" for Tesla).

    Returns:
        dict: A dictionary containing stock information, or None if an error occurs.
    """
    try:
        # Check and handle rate limits before making the API call
        rate_limit_check()

        # Fetch company overview data from Alpha Vantage
        overview_url = "https://www.alphavantage.co/query"
        overview_params = {
            "function": "OVERVIEW",  # API function to get company overview
            "symbol": symbol,  # Stock symbol
            "apikey": ALPHA_VANTAGE_API_KEY,  # API key for authentication
        }
        overview_response = requests.get(overview_url, params=overview_params)
        overview_data = overview_response.json()  # Parse the JSON response

        # If the response does not contain the "Symbol" key, raise an error
        if "Symbol" not in overview_data:
            raise ValueError(f"Unable to fetch data for symbol: {symbol}. Response: {overview_data}")

        # Fetch earnings data from Alpha Vantage
        rate_limit_check()  # Check rate limits before making another API call
        earnings_url = "https://www.alphavantage.co/query"
        earnings_params = {
            "function": "EARNINGS",  # API function to get earnings data
            "symbol": symbol,  # Stock symbol
            "apikey": ALPHA_VANTAGE_API_KEY,  # API key for authentication
        }
        earnings_response = requests.get(earnings_url, params=earnings_params)
        earnings_data = earnings_response.json()  # Parse the JSON response

        # Extract the most recent fiscal quarter from the earnings data
        recent_quarter = "N/A"
        if "quarterlyEarnings" in earnings_data:
            recent_quarter = earnings_data["quarterlyEarnings"][0]["fiscalDateEnding"]

        # Build a dictionary containing the stock information
        stock_info = {
            "symbol": symbol,
            "long_name": overview_data.get("Name", "N/A"),  # Company name
            "sector": overview_data.get("Sector", "N/A"),  # Sector (e.g., "Technology")
            "industry": overview_data.get("Industry", "N/A"),  # Industry (e.g., "Software")
            "market_cap": overview_data.get("MarketCapitalization", "N/A"),  # Market capitalization
            "pe_ratio": overview_data.get("PERatio", "N/A"),  # Price-to-earnings ratio
            "dividend_yield": overview_data.get("DividendYield", "N/A"),  # Dividend yield
            "current_price": overview_data.get("50DayMovingAverage", "N/A"),  # Approximation of current price
            "recent_quarter": recent_quarter,  # Most recent fiscal quarter
        }

        return stock_info  # Return the stock information
    except ValueError as ve:
        # Handle specific errors related to missing or invalid data
        print(f"ValueError: {ve}")
        with open("error_log.txt", "a") as log_file:
            log_file.write(f"{datetime.now()} - ValueError: {ve}\n")
        return None
    except Exception as e:
        # Handle general errors (e.g., network issues)
        print(f"Error fetching data for {symbol}: {e}")
        with open("error_log.txt", "a") as log_file:
            log_file.write(f"{datetime.now()} - Error: {e}\n")
        return None

def analyze_stock_data(stock_data):
    """
    Analyze stock data and provide a Buy, Sell, or Hold recommendation
    based on the price-to-earnings (P/E) ratio.

    Args:
        stock_data (dict): A dictionary containing stock information.

    Returns:
        str: A recommendation ("Buy", "Sell", "Hold", or "No Rating").
    """
    try:
        # Extract the P/E ratio from the stock data
        pe_ratio = stock_data.get("pe_ratio", None)

        # Provide a recommendation based on the P/E ratio
        if pe_ratio is None or pe_ratio == "N/A":
            return "No Rating (P/E ratio unavailable)"
        elif float(pe_ratio) < 15:
            return "Buy"
        elif 15 <= float(pe_ratio) <= 25:
            return "Hold"
        else:
            return "Sell"
    except Exception as e:
        # Handle errors during analysis (e.g., invalid data types)
        print(f"Error analyzing stock data: {e}")
        return "Unable to provide a rating."

# Function to create an interactive dashboard
def interactive_dashboard():
    """
    Create an interactive dashboard using Streamlit.
    """
    # Set the title and description of the dashboard
    st.title("Stock Analysis Dashboard")
    st.write("Analyze stock data interactively by entering stock symbols below.")

    # Input field for stock symbols
    symbols = st.text_input("Enter stock symbol(s) (comma-separated):").upper().strip()

    # Check if the user has entered any symbols
    if symbols:
        # Split the input into a list of symbols
        symbols = symbols.split(",")

        # Process each symbol
        for symbol in symbols:
            symbol = symbol.strip()  # Remove any extra spaces
            if not symbol:  # Skip empty inputs
                continue

            # Fetch stock data
            stock_data = fetch_stock_data(symbol)
            if not stock_data:
                st.error(f"Unable to fetch data for {symbol}.")
                continue

            # Analyze stock data
            rating = analyze_stock_data(stock_data)

            # Display stock information
            st.subheader(f"Analysis for {symbol}")
            st.write("### Stock Information")
            for key, value in stock_data.items():
                st.write(f"**{key.capitalize()}**: {value}")
            st.write("### Rating")
            st.write(f"The rating for {symbol} is: **{rating}**")

def handle_output(display_option, symbol, stock_data, rating, csv_writer=None, html_file=None):
    """
    Handle the output of stock analysis based on the selected display option.
    """
    if display_option == "console":
        # Print the analysis to the console
        print(f"\n=== Analysis for {symbol} ===")
        print("=== Stock Information ===")
        for key, value in stock_data.items():
            print(f"{key.capitalize()}: {value}")
        print("\n=== Rating ===")
        print(f"The rating for {symbol} is: {rating}\n")
    elif display_option == "multiple":
        # Save each stock's analysis in a separate file
        output_file = f"{symbol}_analysis.txt"
        with open(output_file, "w") as file:
            file.write("=== Stock Information ===\n")
            for key, value in stock_data.items():
                file.write(f"{key.capitalize()}: {value}\n")
            file.write("\n=== Rating ===\n")
            file.write(f"The rating for {symbol} is: {rating}\n\n")
        print(f"Analysis for {symbol} has been saved to {output_file}.")
    elif display_option == "one":
        # Append each stock's analysis to a single file
        with open("stock_analysis.txt", "a") as file:
            file.write(f"=== Analysis for {symbol} ===\n")
            file.write("=== Stock Information ===\n")
            for key, value in stock_data.items():
                file.write(f"{key.capitalize()}: {value}\n")
            file.write("\n=== Rating ===\n")
            file.write(f"The rating for {symbol} is: {rating}\n\n")
        print(f"Analysis for {symbol} has been added to stock_analysis.txt.")
    elif display_option == "csv" and csv_writer:
        # Write the stock data to the CSV file
        csv_writer.writerow([
            stock_data.get("symbol", "N/A"),
            stock_data.get("long_name", "N/A"),
            stock_data.get("sector", "N/A"),
            stock_data.get("industry", "N/A"),
            stock_data.get("market_cap", "N/A"),
            stock_data.get("pe_ratio", "N/A"),
            stock_data.get("dividend_yield", "N/A"),
            stock_data.get("current_price", "N/A"),
            stock_data.get("recent_quarter", "N/A"),
            rating,
        ])
        print(f"Analysis for {symbol} has been added to stock_analysis.csv.")
    elif display_option == "html" and html_file:
        # Write the stock data to the HTML file
        html_file.write(f"<h2>Analysis for {symbol}</h2>")
        html_file.write("<ul>")
        for key, value in stock_data.items():
            html_file.write(f"<li><strong>{key.capitalize()}:</strong> {value}</li>")
        html_file.write(f"<li><strong>Rating:</strong> {rating}</li>")
        html_file.write("</ul>")
        print(f"Analysis for {symbol} has been added to stock_analysis.html.")

# Modify the main function to include the dashboard option
def main():
    """
    Main program execution.
    """
    # Display a menu with explanations for each option
    print("\nHow do you want to display the stock analyses?")
    print("1. Console: Display the analysis directly in the terminal.")
    print("2. One: Save all analyses in a single text file (stock_analysis.txt).")
    print("3. Multiple: Save each stock's analysis in separate text files (e.g., TSLA_analysis.txt).")
    print("4. CSV: Save all analyses in a structured CSV file (stock_analysis.csv).")
    print("5. HTML: Generate a styled HTML report (stock_analysis.html).")
    print("6. Dashboard: Launch an interactive web-based dashboard.")

    # Ask the user to choose an option
    display_option = input("Enter your choice (1/2/3/4/5/6): ").strip()

    # Map the user's choice to the corresponding option
    option_map = {
        "1": "console",
        "2": "one",
        "3": "multiple",
        "4": "csv",
        "5": "html",
        "6": "dashboard",
    }
    display_option = option_map.get(display_option, "multiple")  # Default to "multiple" if input is invalid

    if display_option == "dashboard":
        print("Launching the interactive dashboard...")
        interactive_dashboard()
        return False  # Exit the CLI loop since the dashboard runs independently

    # Get user input for stock symbols (comma-separated or single)
    symbols = input(
        "Enter stock symbol(s) (comma-separated for multiple, or press Enter to exit): "
    ).upper().strip()

    # If the user presses Enter without typing anything, exit the program
    if not symbols:
        print("Exiting the program. Goodbye!")
        return False  # Signal to exit the program

    # Split the input into a list of symbols
    symbols = symbols.split(",")

    # If saving to a single document, open the file once
    if display_option == "one":
        output_file = "stock_analysis.txt"
        with open(output_file, "w") as file:
            file.write("=== Stock Analysis ===\n\n")
    elif display_option == "csv":
        # Open the CSV file and write the header
        import csv
        csv_file = open("stock_analysis.csv", "w", newline="")
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(
            ["Symbol", "Long Name", "Sector", "Industry", "Market Cap", "P/E Ratio", "Dividend Yield", "Current Price", "Recent Quarter", "Rating"]
        )
    elif display_option == "html":
        # Open the HTML file and write the header
        html_file = open("stock_analysis.html", "w")
        html_file.write("<html><head><title>Stock Analysis</title></head><body>")
        html_file.write("<h1>Stock Analysis</h1>")

    # Process each symbol
    for symbol in symbols:
        symbol = symbol.strip()  # Remove any extra spaces
        if not symbol:  # Skip empty inputs
            continue

        # Fetch stock data using Alpha Vantage
        stock_data = fetch_stock_data(symbol)
        if not stock_data:
            print(f"Unable to fetch data for {symbol}. Skipping...")
            continue

        # Analyze stock data to determine Buy, Sell, or Hold
        rating = analyze_stock_data(stock_data)

        # Handle the chosen display option
        handle_output(display_option, symbol, stock_data, rating, csv_writer, html_file)

    # Close any open files
    if display_option == "csv":
        csv_file.close()
    elif display_option == "html":
        html_file.write("</body></html>")
        html_file.close()

    return True  # Signal to continue the program


# Entry point
if __name__ == "__main__":
    try:
        while True:  # Loop to allow rerunning the program
            should_continue = main()
            if not should_continue:  # Exit if the user entered 'stop', 'exit', or 'done'
                break
            # Ask the user if they want to run the program again
            rerun = input("Do you want to analyze more stock symbols? (yes/no): ").strip().lower()
            if rerun not in ["yes", "y"]:
                print("Exiting the program. Goodbye!")
                break
    except Exception as e:
        print(f"An unexpected error occurred: {e}")