import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import bodyParser from 'body-parser';
import { Low } from 'lowdb';
import { JSONFile } from 'lowdb/node';
import bcrypt from 'bcryptjs';
import session from 'express-session';
import multer from 'multer';
import fs from 'fs';
import natural from 'natural';
import { createRequire } from 'module';
import { NlpManager } from 'node-nlp';
import nlp from 'compromise';
import rateLimit from 'express-rate-limit';
const require = createRequire(import.meta.url);

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const port = process.env.PORT || 3000;

const adapter = new JSONFile('db.json');

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

const finnhub = require('finnhub');
const api_key = finnhub.ApiClient.instance.authentications['api_key'];
api_key.apiKey = "cvg5nkpr01qgvsqnn8sgcvg5nkpr01qgvsqnn8t0"
const finnhubClient = new finnhub.DefaultApi()

app.use(express.static(path.join(__dirname, 'public')));

const { GoogleGenerativeAI } = require("@google/generative-ai");
const genAI = new GoogleGenerativeAI("AIzaSyCu7_lNOEGQfPdY2kLcJXHXFB7we6kbeC0");



const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash" });

const limiter = rateLimit({
    windowMs: 60 * 1000,
    max: 60,
    message: 'Too many requests from this IP, please try again later.'
});

app.use('/api/', limiter);

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', '/app/main/','home.html'));
});

app.get('/api/stock/:ticker', async(req, res) => {
    const ticker = req.params.ticker;
    
    try {
        console.log(`Fetching company profile for ${ticker}`);
        
        const data = await new Promise((resolve, reject) => {
            finnhubClient.companyProfile2({'symbol': ticker}, (error, data, response) => {
                if (error) {
                    console.error(`Error fetching company profile for ${ticker}:`, error);
                    reject(error);
                } else if (!data || Object.keys(data).length === 0) {
                    console.error(`No data received for ${ticker}`);
                    reject(new Error('No data received from API'));
                } else {
                    console.log(`Successfully fetched company profile for ${ticker}`);
                    resolve(data);
                }
            });
        });
        
        res.json(data);
    } catch (error) {
        console.error(`Server Error for ${ticker}:`, error);
        res.status(500).json({ 
            error: error.message,
            ticker: ticker
        });
    }
});

// Add new endpoint for company news
app.get('/api/stock/:ticker/news', async(req, res) => {
    const ticker = req.params.ticker;
    
    try {
        console.log(`Fetching news for ${ticker}`);
        
        // Get current date and date 30 days ago
        const endDate = new Date().toISOString().split('T')[0];
        const startDate = new Date();
        startDate.setDate(startDate.getDate() - 30);
        const formattedStartDate = startDate.toISOString().split('T')[0];
        
        const newsData = await new Promise((resolve, reject) => {
            finnhubClient.companyNews(ticker, formattedStartDate, endDate, (error, data, response) => {
                if (error) {
                    console.error(`Error fetching news for ${ticker}:`, error);
                    reject(error);
                } else if (!data || data.length === 0) {
                    console.error(`No news data received for ${ticker}`);
                    reject(new Error('No news data received from API'));
                } else {
                    console.log(`Successfully fetched news for ${ticker}`);
                    resolve(data);
                }
            });
        });
        
        res.json(newsData);
    } catch (error) {
        console.error(`Server Error fetching news for ${ticker}:`, error);
        res.status(500).json({ 
            error: error.message,
            ticker: ticker
        });
    }
});

// Cache for stock prices
let stockPriceCache = {};
const CACHE_FILE = path.join(__dirname, 'stock_price_cache.json');

// Load cache from file if it exists
try {
    if (fs.existsSync(CACHE_FILE)) {
        stockPriceCache = JSON.parse(fs.readFileSync(CACHE_FILE, 'utf8'));
    }
} catch (error) {
    console.error('Error loading price cache:', error);
}

// Function to update stock prices
async function updateStockPrices() {
    const tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'JPM', 'V', 'WMT'];
    
    for (const symbol of tickers) {
        try {
            // Get quote data which includes previous close and current price
            const quoteData = await new Promise((resolve, reject) => {
                finnhubClient.quote(symbol, (error, data, response) => {
                    if (error) reject(error);
                    else resolve(data);
                });
            });

            if (quoteData && quoteData.c) { // c is current price
                const currentPrice = quoteData.c;
                const previousClose = quoteData.pc; // pc is previous close
                const percentChange = previousClose ? ((currentPrice - previousClose) / previousClose) * 100 : 0;

                stockPriceCache[symbol] = {
                    price: currentPrice,
                    percentChange: percentChange,
                    lastUpdated: new Date().toISOString()
                };
            }
        } catch (error) {
            console.error(`Error updating price for ${symbol}:`, error);
        }
    }
    
    // Save cache to file
    try {
        fs.writeFileSync(CACHE_FILE, JSON.stringify(stockPriceCache, null, 2));
    } catch (error) {
        console.error('Error saving price cache:', error);
    }
}

// Update prices every 10 minutes
setInterval(updateStockPrices, 10 * 60 * 1000);

// Initial update
updateStockPrices();

// Add new endpoint for cached prices
app.get('/api/stock-prices', (req, res) => {
    res.json(stockPriceCache);
});

// Add new endpoint for sentiment analysis
app.post('/api/stock/:ticker/sentiment', async(req, res) => {
    const ticker = req.params.ticker;
    
    try {
        console.log(`Fetching news for sentiment analysis of ${ticker}`);
        
        // Get current date and date 14 days ago
        const endDate = new Date().toISOString().split('T')[0];
        const startDate = new Date();
        startDate.setDate(startDate.getDate() - 14);
        const formattedStartDate = startDate.toISOString().split('T')[0];
        
        const newsData = await new Promise((resolve, reject) => {
            finnhubClient.companyNews(ticker, formattedStartDate, endDate, (error, data, response) => {
                if (error) {
                    console.error(`Error fetching news for ${ticker}:`, error);
                    reject(error);
                } else if (!data || data.length === 0) {
                    console.error(`No news data received for ${ticker}`);
                    reject(new Error('No news data received from API'));
                } else {
                    console.log(`Successfully fetched news for ${ticker}`);
                    resolve(data);
                }
            });
        });

        // Create a prompt with the news articles
        const newsContext = newsData.slice(0, 5).map(article => 
            `Headline: ${article.headline}\nSummary: ${article.summary || 'No summary available'}\n`
        ).join('\n');

        const prompt = `Based on these recent news articles about ${ticker} from the last 14 days, provide a concise (1-2 sentences) analysis of current market sentiment. Focus on:

1. Recent significant developments or announcements that could impact the stock
2. Specific market reactions or price movements mentioned in the news
3. Notable analyst opinions or institutional investor actions
4. Any immediate catalysts or risks mentioned

Here are the articles:

${newsContext}

Please be specific and avoid generic market commentary. Focus on concrete information from the articles.`;

        // Generate sentiment analysis
        const result = await model.generateContent(prompt);
        const response = await result.response;
        
        res.json({ 
            sentiment: response.text(),
            prompt,
            newsLinks: newsData.slice(0, 5).map(article => ({
                url: article.url,
                headline: article.headline,
                summary: article.summary
            }))
        });
    } catch (error) {
        console.error(`Server Error analyzing sentiment for ${ticker}:`, error);
        res.status(500).json({ 
            error: error.message,
            ticker: ticker
        });
    }
});

// Add risk analysis endpoint
app.post('/api/stock/:ticker/risk', async(req, res) => {
    const ticker = req.params.ticker;
    
    try {
        console.log(`Analyzing risk for ${ticker}`);
        
        // Get current date and date 14 days ago
        const endDate = new Date().toISOString().split('T')[0];
        const startDate = new Date();
        startDate.setDate(startDate.getDate() - 14);
        const formattedStartDate = startDate.toISOString().split('T')[0];
        
        // Get news data
        const newsData = await new Promise((resolve, reject) => {
            finnhubClient.companyNews(ticker, formattedStartDate, endDate, (error, data, response) => {
                if (error) reject(error);
                else resolve(data);
            });
        });

        // Get current stock price and historical data
        const quoteData = await new Promise((resolve, reject) => {
            finnhubClient.quote(ticker, (error, data, response) => {
                if (error) reject(error);
                else resolve(data);
            });
        });

        // Create a prompt for risk analysis
        const newsContext = newsData.slice(0, 5).map(article => 
            `Headline: ${article.headline}\nSummary: ${article.summary || 'No summary available'}\n`
        ).join('\n');

        const prompt = `Based on the following information about ${ticker}, analyze the current investment risk level and provide:
1. A risk score from 0-100 (where 0 is lowest risk, 100 is highest risk)
2. A brief explanation of the key risk factors

Consider:
- Recent news and developments
- Market volatility
- Company-specific risks
- Industry trends
- Economic conditions

Current Price: ${quoteData.c}
Previous Close: ${quoteData.pc}
Day High: ${quoteData.h}
Day Low: ${quoteData.l}

Recent News:
${newsContext}

Please provide the response in this exact format:
RISK_SCORE: [number]
EXPLANATION: [2-3 sentences]`;

        // Generate risk analysis using Gemini
        const result = await model.generateContent(prompt);
        const response = await result.response;
        const analysis = response.text();
        
        // Parse the response
        const riskScore = parseInt(analysis.match(/RISK_SCORE:\s*(\d+)/)[1]);
        const explanation = analysis.match(/EXPLANATION:\s*(.*)/)[1].trim();
        
        res.json({ 
            riskScore,
            explanation,
            prompt
        });
    } catch (error) {
        console.error(`Server Error analyzing risk for ${ticker}:`, error);
        res.status(500).json({ 
            error: error.message,
            ticker: ticker
        });
    }
});

app.listen(port, '0.0.0.0', () => {
    console.log(`Server running on port ${port}`);
});