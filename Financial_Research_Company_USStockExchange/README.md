# Stock Analysis Dashboard

## Overview

Stock Analysis Dashboard is a comprehensive web application that provides in-depth analysis of US stocks, delivering financial metrics, technical indicators, news sentiment, and more in an intuitive interface. Built for both casual investors and financial professionals, this tool offers a consolidated view of critical stock information to support informed investment decisions.

## Features

### 📊 Interactive Price Charts

- Candlestick and line charts with customizable time ranges
- Technical overlays (50-day SMA)
- Volume analysis
- Key price statistics

### 📈 Technical Analysis

- RSI (Relative Strength Index) calculations and visualization
- Moving Average analysis
- Overall technical signals with detailed explanations
- Visual indicators of overbought/oversold conditions

### 💰 Financial Metrics

- Revenue, EPS, and Net Income tracking
- Balance sheet health assessment
- Debt-to-Asset ratio analysis
- Visual health indicators

### 📰 News Sentiment Analysis

- Recent news aggregation with summary
- Sentiment scoring based on keyword analysis
- Visual sentiment gauge
- Sentiment trend analysis

### 💵 Dividend Information

- Current dividend yield calculation
- Payment history visualization
- Ex-dividend and payment dates

### 👥 Analyst Recommendations

- Consensus ratings visualization
- Buy/Hold/Sell distribution
- Rating trends

## Installation

### Prerequisites

- Python 3.8 or higher
- Pip package manager

### Steps

1. Clone the repository:

```bash
git clone https://github.com/yourusername/stock-analysis-dashboard.git
cd stock-analysis-dashboard
```

2. Create and activate a virtual environment (optional but recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required packages:

```bash
pip install -r requirements.txt
```

4. Set up API credentials:
   - Copy `.env.sample` to `.env`
   - Add your Polygon API key and OpenAI API key to the `.env` file

## Usage

1. Start the Streamlit application:

```bash
streamlit run app.py
```

2. Access the dashboard in your web browser at `http://localhost:8501`

3. Enter a stock ticker (e.g., AAPL, MSFT, GOOGL) in the sidebar and click "Analyze Stock"

4. Navigate through the various sections using the top navigation bar

## Technologies Used

- **[Streamlit](https://streamlit.io/)**: Frontend web application framework
- **[Plotly](https://plotly.com/)**: Interactive data visualization
- **[Pandas](https://pandas.pydata.org/)**: Data manipulation and analysis
- **[NumPy](https://numpy.org/)**: Numerical computations
- **[Polygon.io](https://polygon.io/)**: Financial data API
- **[ReportLab](https://www.reportlab.com/)**: PDF report generation

## Project Structure

```
├── app.py                    # Main Streamlit application
├── InfoFetch.py              # Stock data retrieval module
├── ReportGeneration.py       # PDF report generation functionality
├── requirements.txt          # Required Python packages
├── .env.sample               # Sample environment variables file
└── cache/                    # Data cache directory
    └── *_data.json           # Cached stock data
```

## Disclaimer

This dashboard is provided for informational purposes only. It is not intended to provide investment advice, and users should conduct their own research before making investment decisions.
