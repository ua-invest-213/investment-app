const express = require('express');
const router = express.Router();
const { Configuration, OpenAIApi } = require('openai');
const { GoogleGenerativeAI } = require('@google/generative-ai');
const { getCompanyProfile, getCompanyPeers } = require('../services/finnhub');
const { analyzeRisk } = require('../services/riskAnalysis');

router.get('/:ticker', async (req, res) => {
    try {
        const profile = await getCompanyProfile(req.params.ticker);
        res.json(profile);
    } catch (error) {
        console.error('Error fetching company profile:', error);
        res.status(500).json({ error: 'Failed to fetch company profile' });
    }
});

router.post('/:ticker/sentiment', async (req, res) => {
    try {
        const { modelType, openAIToken } = req.body;
        const ticker = req.params.ticker;
        const profile = await getCompanyProfile(ticker);

        let sentiment;
        let prompt;

        if (modelType === 'gpt-4') {
            if (!openAIToken) {
                return res.status(400).json({ error: 'OpenAI API token is required for GPT-4' });
            }

            try {
                const configuration = new Configuration({
                    apiKey: openAIToken,
                });
                const openai = new OpenAIApi(configuration);

                prompt = `Analyze the market sentiment for ${profile.name} (${profile.ticker}) based on the following information:
                Industry: ${profile.finnhubIndustry}
                Market Cap: ${profile.marketCapitalization}
                Exchange: ${profile.exchange}
                Country: ${profile.country}
                
                Provide a concise analysis of the company's current market position and potential future outlook.`;

                const completion = await openai.createChatCompletion({
                    model: "gpt-4",
                    messages: [{ role: "user", content: prompt }],
                    max_tokens: 500,
                    temperature: 0.7,
                });

                sentiment = completion.data.choices[0].message.content;
            } catch (error) {
                if (error.response?.status === 401) {
                    return res.status(401).json({ error: 'Invalid OpenAI API token' });
                }
                throw error;
            }
        } else {
            const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
            const model = genAI.getGenerativeModel({ model: "gemini-pro" });

            prompt = `Analyze the market sentiment for ${profile.name} (${profile.ticker}) based on the following information:
            Industry: ${profile.finnhubIndustry}
            Market Cap: ${profile.marketCapitalization}
            Exchange: ${profile.exchange}
            Country: ${profile.country}
            
            Provide a concise analysis of the company's current market position and potential future outlook.`;

            const result = await model.generateContent(prompt);
            sentiment = result.response.text();
        }

        res.json({ sentiment, prompt });
    } catch (error) {
        console.error('Error analyzing sentiment:', error);
        res.status(500).json({ error: 'Failed to analyze market sentiment' });
    }
});

router.post('/:ticker/risk', async (req, res) => {
    try {
        const riskAnalysis = await analyzeRisk(req.params.ticker);
        res.json(riskAnalysis);
    } catch (error) {
        console.error('Error analyzing risk:', error);
        res.status(500).json({ error: 'Failed to analyze investment risk' });
    }
});

router.post('/:ticker/peers', async (req, res) => {
    try {
        const peers = await getCompanyPeers(req.params.ticker);
        res.json({ peers });
    } catch (error) {
        console.error('Error fetching peer companies:', error);
        res.status(500).json({ error: 'Failed to fetch peer companies' });
    }
});

module.exports = router; 