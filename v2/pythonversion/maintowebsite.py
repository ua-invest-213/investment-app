# Import necessary libraries
import openai  # For OpenAI API integration
import requests  # For making HTTP requests to the Alpha Vantage API
from datetime import datetime  # For handling timestamps and logging
from dotenv import load_dotenv, find_dotenv  # For loading environment variables from a .env file
import os  # For interacting with the operating system (e.g., reading environment variables)
from flask import Flask, render_template, request  # For creating the web app
from stockthing.v2.pythonversion.stock_analysis import fetch_stock_data, analyze_stock_data  # Custom modules
from stockthing.v2.pythonversion.utils import rate_limit_check  # Utility functions

# Load the .env file to access API keys
dotenv_path = find_dotenv("api.env")
if dotenv_path:
    load_dotenv(dotenv_path)

# Access the environment variables for API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()  # OpenAI API key
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "").strip()  # Alpha Vantage API key

# Set the OpenAI API key
openai.api_key = OPENAI_API_KEY

# Initialize Flask app
app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    """
    Homepage where users can input stock symbols and get analysis.
    """
    if request.method == "POST":
        # Get user input
        stock_symbol = request.form.get("stock_symbol").upper().strip()

        # Fetch stock data
        stock_data = fetch_stock_data(stock_symbol, ALPHA_VANTAGE_API_KEY)
        if not stock_data:
            return render_template("index.html", error="Unable to fetch stock data. Please check the symbol.")

        # Analyze stock data
        rating = analyze_stock_data(stock_data)

        # Fetch investor sentiment
        sentiment = get_investor_sentiment(stock_symbol)

        # Fetch competing companies
        competitors = get_competing_companies(stock_symbol)

        # Render the result page
        return render_template(
            "result.html",
            stock_data=stock_data,
            rating=rating,
            sentiment=sentiment,
            competitors=competitors,
        )

    return render_template("index.html")

def get_investor_sentiment(stock_symbol):
    """
    Use web scraping and ChatGPT to analyze investor sentiment for the given stock symbol.
    """
    try:
        # Simulate web scraping (replace this with actual scraping logic)
        articles = [
            f"Article 1 about {stock_symbol}",
            f"Article 2 about {stock_symbol}",
            f"Article 3 about {stock_symbol}",
        ]

        # Use ChatGPT to analyze sentiment
        prompt = (
            f"Analyze the sentiment of the following articles about {stock_symbol}:\n\n"
            + "\n".join(articles)
            + "\n\nProvide a summary of the overall sentiment (positive, negative, or neutral) and key points."
        )
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=200,
            temperature=0.7,
        )
        return response.choices[0].text.strip()
    except Exception as e:
        print(f"Error fetching investor sentiment: {e}")
        return "Unable to fetch investor sentiment."

def get_competing_companies(stock_symbol):
    """
    Use ChatGPT to identify competing companies and fetch their stock information.
    """
    try:
        # Use ChatGPT to identify competitors
        prompt = (
            f"Identify the main competitors of the company with stock symbol {stock_symbol}. "
            "Provide their stock symbols."
        )
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=100,
            temperature=0.7,
        )
        competitors = response.choices[0].text.strip().split(",")  # Assume competitors are comma-separated

        # Fetch stock data for each competitor
        competitor_data = []
        for competitor in competitors:
            competitor = competitor.strip()
            stock_data = fetch_stock_data(competitor, ALPHA_VANTAGE_API_KEY)
            if stock_data:
                competitor_data.append(stock_data)

        return competitor_data
    except Exception as e:
        print(f"Error fetching competing companies: {e}")
        return []

if __name__ == "__main__":
    # Start the Flask app instead of running the CLI
    app.run(debug=True)