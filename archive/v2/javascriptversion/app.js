const express = require("express");
const axios = require("axios");
const dotenv = require("dotenv");
const path = require("path");

// Load environment variables from api.env
dotenv.config({ path: path.join(__dirname, "api.env") });

const app = express();
const PORT = process.env.PORT || 3000;

// Save API key to a variable
const ALPHA_VANTAGE_API_KEY = process.env.ALPHA_VANTAGE_API_KEY;

// Middleware to parse form data
app.use(express.urlencoded({ extended: true }));
app.use(express.json());

// Set EJS as the templating engine
app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "views"));

// Serve static files (CSS, JS)
app.use(express.static(path.join(__dirname, "public")));

// Homepage route
app.get("/", (req, res) => {
  res.render("index");
});

// Handle form submission
app.post("/analyze", async (req, res) => {
  const stockSymbol = req.body.stock_symbol.toUpperCase();

  try {
    // Fetch stock data from Alpha Vantage
    const stockData = await fetchStockData(stockSymbol);

    // Analyze stock data
    const rating = analyzeStockData(stockData);

    // Render the result page
    res.render("result", {
      stockData,
      rating,
    });
  } catch (error) {
    console.error("Error:", error.message);
    res.render("index", { error: "Unable to fetch stock data. Please try again." });
  }
});

// Fetch stock data from Alpha Vantage
async function fetchStockData(symbol) {
  const url = `https://www.alphavantage.co/query?function=OVERVIEW&symbol=${symbol}&apikey=${ALPHA_VANTAGE_API_KEY}`;

  const response = await axios.get(url);
  if (response.data && response.data.Symbol) {
    return {
      symbol: response.data.Symbol,
      long_name: response.data.Name,
      sector: response.data.Sector,
      industry: response.data.Industry,
      market_cap: response.data.MarketCapitalization,
      pe_ratio: response.data.PERatio,
      dividend_yield: response.data.DividendYield,
    };
  } else {
    throw new Error("Invalid stock symbol or API error.");
  }
}

// Analyze stock data
function analyzeStockData(stockData) {
  const peRatio = parseFloat(stockData.pe_ratio);
  if (isNaN(peRatio)) return "No Rating (P/E ratio unavailable)";
  if (peRatio < 15) return "Buy";
  if (peRatio <= 25) return "Hold";
  return "Sell";
}

// Start the server
app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});
