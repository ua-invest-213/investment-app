from flask import Flask, render_template, request
from stockthing.v2.pythonversion.stock_analysis import fetch_stock_data, analyze_stock_data
from dotenv import load_dotenv
import os

# Initialize Flask app
app = Flask(__name__)

# Load environment variables
load_dotenv("api.env")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "").strip()

@app.route("/", methods=["GET", "POST"])
def index():
    """
    Homepage where users can input stock symbols and API keys.
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

        # Render the result page
        return render_template("result.html", stock_data=stock_data, rating=rating)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)