# Import necessary libraries
import openai  # For OpenAI API integration (currently unused in this script)
import requests  # For making HTTP requests to the Alpha Vantage API
from datetime import datetime  # For handling timestamps and logging
from dotenv import load_dotenv, find_dotenv  # For loading environment variables from a .env file
import os  # For interacting with the operating system (e.g., reading environment variables)
import time  # For handling rate-limiting and delays

from stockthing.v2.pythonversion.stock_analysis import fetch_stock_data, analyze_stock_data
from output_handler import handle_output
from stockthing.v2.pythonversion.utils import rate_limit_check

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

def main():
    print("\nHow do you want to display the stock analyses?")
    print("1. Console: Display the analysis directly in the terminal.")
    print("2. One: Save all analyses in a single text file (stock_analysis.txt).")
    print("3. Multiple: Save each stock's analysis in separate text files (e.g., TSLA_analysis.txt).")
    print("4. CSV: Save all analyses in a structured CSV file (stock_analysis.csv).")

    display_option = input("Enter your choice (1/2/3/4): ").strip()
    option_map = {"1": "console", "2": "one", "3": "multiple", "4": "csv"}
    display_option = option_map.get(display_option, "multiple")

    symbols = input("Enter stock symbol(s) (comma-separated for multiple, or press Enter to exit): ").upper().strip()
    if not symbols:
        print("Exiting the program. Goodbye!")
        return False

    symbols = symbols.split(",")
    for symbol in symbols:
        # Pass the API key from the environment variables
        stock_data = fetch_stock_data(symbol, ALPHA_VANTAGE_API_KEY)
        if not stock_data:
            print(f"Unable to fetch data for {symbol}. Skipping...")
            continue
        rating = analyze_stock_data(stock_data)
        handle_output(display_option, symbol, stock_data, rating)

if __name__ == "__main__":
    main()