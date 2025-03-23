let currentPrompt = '';

function formatMarketCap(value) {
    if (!value) return 'N/A';
    
    const valueInMillions = value;
    
    if (valueInMillions >= 1000000) {
        return `$${(valueInMillions / 1000000).toFixed(2)}T`;
    } else if (valueInMillions >= 1000) {
        return `$${(valueInMillions / 1000).toFixed(2)}B`;
    } else if (valueInMillions >= 1) {
        return `$${valueInMillions.toFixed(2)}M`;
    } else {
        return `$${valueInMillions.toFixed(2)}M`;
    }
}

async function search() {
    const ticker = document.getElementById('tickerInput').value.toUpperCase();
    if (!ticker) {
        showError('Please enter a stock symbol');
        return;
    }

    // Show loading overlay
    document.querySelector('.loading-overlay').classList.add('active');

    try {
        // Reset previous data
        document.getElementById('newsData').innerHTML = '';
        document.getElementById('riskExplanation').textContent = '';
        document.querySelector('.risk-score').textContent = '0';
        document.querySelector('.thermometer-fill').style.height = '0%';
        document.getElementById('companyLogo').style.display = 'none';

        // Fetch company profile and sentiment data
        const response = await fetch(`/api/stock/${ticker}`);
        if (!response.ok) {
            throw new Error('Failed to fetch company data');
        }
        
        const data = await response.json();
        
        // Display company profile
        const profileHtml = `
            <h2>${data.name} (${data.ticker})</h2>
            <p><strong>Industry:</strong> ${data.finnhubIndustry || 'N/A'}</p>
            <p><strong>Exchange:</strong> ${data.exchange || 'N/A'}</p>
            <p><strong>Currency:</strong> ${data.currency || 'N/A'}</p>
            <p><strong>Country:</strong> ${data.country || 'N/A'}</p>
            <p><strong>Market Cap:</strong> ${formatMarketCap(data.marketCapitalization)}</p>
            <p><strong>Share Outstanding:</strong> ${data.shareOutstanding ? (data.shareOutstanding / 1000000).toFixed(2) + 'M' : 'N/A'}</p>
            <p><strong>IPO Date:</strong> ${data.ipo ? new Date(data.ipo).toLocaleDateString() : 'N/A'}</p>
            <p><strong>Phone:</strong> ${data.phone || 'N/A'}</p>
            <p><strong>Website:</strong> ${data.weburl ? `<a href="${data.weburl}" target="_blank">${data.weburl}</a>` : 'N/A'}</p>
        `;
        document.getElementById('profileData').innerHTML = profileHtml;

        // Fetch and display sentiment analysis
        const sentimentResponse = await fetch(`/api/stock/${ticker}/sentiment`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!sentimentResponse.ok) {
            throw new Error('Failed to fetch sentiment analysis');
        }
        
        const sentimentData = await sentimentResponse.json();
        
        // Display sentiment analysis
        if (!sentimentData || !sentimentData.sentiment) {
            document.getElementById('newsData').innerHTML = '<p>Unable to analyze market sentiment</p>';
        } else {
            const sentimentHtml = `
                <div class="sentiment-analysis">
                    <div class="model-analysis">
                        <h2>Market Sentiment Analysis</h2>
                        <p class="sentiment-text">${sentimentData.sentiment}</p>
                    </div>
                </div>
            `;
            document.getElementById('newsData').innerHTML = sentimentHtml;
            
            // Store the prompt from the server response
            currentPrompt = sentimentData.prompt;
        }

        // Fetch and display risk analysis
        try {
            const riskResponse = await fetch(`/api/stock/${ticker}/risk`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!riskResponse.ok) {
                throw new Error('Failed to fetch risk analysis');
            }
            
            const riskData = await riskResponse.json();
            
            // Update thermometer
            const thermometerFill = document.querySelector('.thermometer-fill');
            const riskScore = document.querySelector('.risk-score');
            const riskExplanation = document.getElementById('riskExplanation');
            
            // Set the fill height based on risk score
            thermometerFill.style.height = `${riskData.riskScore}%`;
            
            // Update the score display
            riskScore.textContent = riskData.riskScore;
            
            // Update the explanation
            riskExplanation.textContent = riskData.explanation;
            
            // Update thermometer color based on risk level
            thermometerFill.classList.remove('low-risk', 'medium-risk', 'high-risk');
            if (riskData.riskScore <= 33) {
                thermometerFill.classList.add('low-risk');
            } else if (riskData.riskScore <= 66) {
                thermometerFill.classList.add('medium-risk');
            } else {
                thermometerFill.classList.add('high-risk');
            }

            // Update company logo using the URL from profile data
            const companyLogo = document.getElementById('companyLogo');
            if (data && data.logo) {
                companyLogo.src = data.logo;
                companyLogo.style.display = 'block';
            } else {
                companyLogo.style.display = 'none';
            }
            
        } catch (err) {
            console.error('Error fetching risk analysis:', err);
            document.getElementById('riskExplanation').textContent = 'Unable to analyze investment risk';
            // Hide logo on error
            document.getElementById('companyLogo').style.display = 'none';
        }

    } catch (err) {
        console.error('Error fetching data:', err);
        showError(`Error fetching data: ${err.message}`);
        document.getElementById('newsData').innerHTML = '<p>Error analyzing market sentiment</p>';
        // Hide logo on error
        document.getElementById('companyLogo').style.display = 'none';
    } finally {
        // Hide loading overlay
        document.querySelector('.loading-overlay').classList.remove('active');
    }
}

function showError(message) {
    const errorDiv = document.getElementById('error');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
}

async function fetchInitialPrices() {
    try {
        const response = await fetch('/api/stock-prices');
        const priceData = await response.json();
        
        Object.entries(priceData).forEach(([symbol, data]) => {
            const tickerItems = document.querySelectorAll('.ticker-item');
            tickerItems.forEach(item => {
                if (item.getAttribute('data-symbol') === symbol) {
                    const priceElement = item.querySelector('.ticker-price');
                    const changeElement = item.querySelector('.ticker-change');
                    
                    if (priceElement) {
                        priceElement.textContent = `$${data.price.toFixed(2)}`;
                    }
                    
                    if (changeElement && data.percentChange !== undefined) {
                        const changeText = data.percentChange >= 0 ? '↑' : '↓';
                        changeElement.textContent = `${changeText} ${Math.abs(data.percentChange).toFixed(2)}%`;
                        changeElement.className = `ticker-change ${data.percentChange >= 0 ? 'positive' : 'negative'}`;
                    }
                }
            });
        });
    } catch (error) {
        console.error('Error fetching initial prices:', error);
    }
}

// Initialize when the page loads
document.addEventListener('DOMContentLoaded', async function() {
    await fetchInitialPrices();
    // Refresh prices every 10 minutes
    setInterval(fetchInitialPrices, 10 * 60 * 1000);

    const showPromptBtn = document.getElementById('showPromptBtn');
    const promptContainer = document.getElementById('promptContainer');
    const promptText = document.querySelector('.prompt-text');

    showPromptBtn.addEventListener('click', function() {
        if (promptContainer.style.display === 'none') {
            promptContainer.style.display = 'block';
            promptText.textContent = currentPrompt;
            showPromptBtn.textContent = 'Hide Prompt';
        } else {
            promptContainer.style.display = 'none';
            showPromptBtn.textContent = 'Show Prompt';
        }
    });
});