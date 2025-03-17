import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime, timedelta
import time
import os
import json
import traceback

# Import your existing stock analyzer code
from InfoFetch import StockAnalyzer

# Set page configuration
st.set_page_config(
    page_title="Stock Analysis Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define color scheme
COLOR_PRIMARY = "#3498db"
COLOR_SECONDARY = "#2980b9"
COLOR_ACCENT = "#1abc9c"
COLOR_BACKGROUND = "#f8f9fa"
COLOR_TEXT = "#2c3e50"
COLOR_POSITIVE = "#27ae60"
COLOR_NEGATIVE = "#e74c3c"
COLOR_NEUTRAL = "#7f8c8d"
COLOR_WARNING = "#f39c12"
COLOR_INFO = "#3498db"

# Update the CSS with fixed text colors for proper visibility and fixed positioning
st.markdown("""
<style>
/* Global styles with improved typography and white text */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    color: white;
}

.main {
    background-color: transparent;
    color: white;
    padding: 0.5rem;
}

/* Force Streamlit elements to use white text */
.css-1offfwp p, .css-1offfwp h1, .css-1offfwp h2, .css-1offfwp h3, 
.css-1offfwp h4, .css-1offfwp h5, .css-1offfwp h6, .css-1offfwp span {
    color: white !important;
}

/* Ensure all paragraphs have white text */
p, h1, h2, h3, h4, h5, h6, span, div {
    color: white;
}

/* More compact header with transparency */
.main-header {
    font-size: 1.8rem;
    color: white;
    font-weight: 700;
    margin-bottom: 1rem;
    text-align: center;
    padding: 0.75rem 0.5rem;
    border-radius: 6px;
    background-color: rgba(52, 152, 219, 0.2);
    border: 1px solid rgba(52, 152, 219, 0.5);
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

/* Improved section headers with better visibility */
.section-header {
    font-size: 1.4rem;
    color: white;
    font-weight: 600;
    margin-top: 1.5rem;
    margin-bottom: 0.8rem;
    padding: 0.5rem 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.2);
    clear: both; /* Prevent overlap with previous elements */
}

.subsection-header {
    font-size: 1.2rem;
    color: white;
    font-weight: 600;
    margin-top: 1rem;
    margin-bottom: 0.5rem;
}

/* Transparent card design with no borders */
.card {
    background-color: transparent;
    border-radius: 6px;
    padding: 0.8rem;
    margin-bottom: 0.8rem;
    border: none;
    color: white;
}

/* More compact metric cards with complete transparency */
.metric-card {
    background-color: transparent;
    border-radius: 6px;
    padding: 0.7rem;
    text-align: center;
    height: 100%;
    border: none;
    color: white;
}

.metric-value {
    font-size: 1.4rem;
    font-weight: bold;
    margin: 0.4rem 0;
    color: white;
}

.metric-label {
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.8);
    font-weight: 500;
    margin-bottom: 0.3rem;
}

/* Explicitly set positive/negative colors */
.positive {
    color: #2ecc71 !important;
}

.negative {
    color: #e74c3c !important;
}

/* Fully transparent info boxes with no borders */
.info-box, .warning-box, .success-box, .error-box {
    background-color: transparent;
    border: none;
    padding: 0.8rem;
    margin: 0.8rem 0;
    color: white;
}

.warning-box {
    color: #f39c12;
}

.success-box {
    color: #27ae60;
}

.error-box {
    color: #e74c3c;
}

/* Compact news cards with transparency */
.news-card {
    background-color: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    padding: 0.8rem;
    margin-bottom: 0.7rem;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: white;
}

.news-title {
    font-size: 1.1rem;
    font-weight: 600;
    margin: 0.5rem 0;
    color: white;
}

.news-date, .news-source {
    color: rgba(255, 255, 255, 0.7);
    font-size: 0.85rem;
}

/* More readable tables with transparency */
.styled-table {
    width: 100%;
    border-collapse: collapse;
    margin: 1rem 0;
    font-size: 0.85rem;
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: white;
    background-color: rgba(255, 255, 255, 0.05);
}

.styled-table td, .styled-table th {
    padding: 0.5rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    color: white;
}

.styled-table thead tr {
    background-color: rgba(52, 152, 219, 0.2);
    color: white;
    text-align: left;
    font-weight: bold;
}

/* Badge styling with improved contrast */
.badge {
    display: inline-block;
    padding: 0.25rem 0.5rem;
    font-size: 0.75rem;
    font-weight: 700;
    line-height: 1;
    text-align: center;
    white-space: nowrap;
    vertical-align: baseline;
    border-radius: 0.375rem;
    background-color: rgba(233, 236, 239, 0.2);
    color: white;
}

.badge-primary {
    background-color: rgba(52, 152, 219, 0.8);
    color: white;
}

.badge-success {
    background-color: rgba(39, 174, 96, 0.8);
    color: white;
}

.badge-danger {
    background-color: rgba(231, 76, 60, 0.8);
    color: white;
}

.badge-info {
    background-color: rgba(52, 152, 219, 0.8);
    color: white;
}

.badge-warning {
    background-color: rgba(243, 156, 18, 0.8);
    color: white;
}

/* Improved tab styling with transparency */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background-color: rgba(255, 255, 255, 0.1);
    padding: 0.3rem;
    border-radius: 6px;
    border: 1px solid rgba(255, 255, 255, 0.2);
}

.stTabs [data-baseweb="tab"] {
    height: auto;
    white-space: pre-wrap;
    background-color: rgba(255, 255, 255, 0.05);
    border-radius: 4px;
    padding: 0.5rem 0.8rem;
    font-weight: 500;
    color: white;
}

.stTabs [aria-selected="true"] {
    background-color: rgba(52, 152, 219, 0.8) !important;
    color: white !important;
    font-weight: bold;
}

/* Enhanced sidebar styling with better visibility */
.css-1lcbmhc.e1fqkh3o0, .css-1d391kg, .css-12oz5g7 {
    background-color: rgba(255, 255, 255, 0.05);
    color: white;
}

.sidebar .sidebar-content, div[data-testid="stSidebarNav"] {
    background-color: rgba(255, 255, 255, 0.05);
    color: white;
}

/* Fix for any white text in Streamlit elements */
.element-container, .stMarkdown, .css-1r6slb0, .css-1ctgxzu {
    color: white !important;
}

/* Improved input fields */
.stTextInput>div>div>input {
    background-color: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 4px;
    padding: 0.5rem;
    font-size: 0.9rem;
    color: white;
}

/* Enhanced buttons with better visibility */
.stButton>button {
    background-color: rgba(52, 152, 219, 0.8);
    color: white !important;
    font-weight: 600;
    border: none;
    border-radius: 4px;
    padding: 0.4rem 0.8rem;
    border: 1px solid rgba(52, 152, 219, 0.8);
}

.stButton>button:hover {
    background-color: rgba(41, 128, 185, 0.9);
    color: white !important;
    border: 1px solid rgba(41, 128, 185, 1);
}

/* Logo text with better visibility */
.logo-text {
    font-size: 1.5rem;
    font-weight: 700;
    color: #3498db;
    text-align: center;
    margin: 1rem 0;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

/* Compact sticky navigation with transparency - FIXED to prevent overlap */
.sticky-nav {
    position: sticky;
    top: 0;
    z-index: 100;
    background-color: rgba(0, 0, 0, 0.7);
    padding: 0.5rem;
    margin: -0.5rem -0.5rem 0.8rem -0.5rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    display: flex;
    justify-content: space-between;
    align-items: center;
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    height: auto; /* Allow height to fit content */
    line-height: normal; /* Fix line height for better text display */
}

.nav-logo {
    font-weight: bold;
    color: white;
    font-size: 1rem;
    display: flex;
    align-items: center;
    gap: 6px;
}

.nav-links {
    display: flex;
    gap: 8px;
    flex-wrap: wrap; /* Allow wrapping for small screens */
}

.nav-link {
    color: rgba(255, 255, 255, 0.8);
    text-decoration: none;
    font-weight: 500;
    padding: 0.4rem 0.6rem;
    border-radius: 4px;
    font-size: 0.85rem;
    transition: all 0.2s ease;
    display: inline-block; /* Fix for alignment */
}

.nav-link:hover {
    background-color: rgba(52, 152, 219, 0.3);
    color: white;
}

.nav-link.active {
    background-color: rgba(52, 152, 219, 0.5);
    color: white;
}

/* Compact loading spinner */
.loading {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 120px;
    flex-direction: column;
    color: white;
    margin: 20px 0; /* Add proper margin */
}

.loading-spinner {
    border: 3px solid rgba(255, 255, 255, 0.1);
    border-radius: 50%;
    border-top: 3px solid #3498db;
    width: 30px;
    height: 30px;
    animation: spin 1s linear infinite;
}

/* Compact welcome screen with glass effect */
.welcome-card {
    background-color: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    padding: 1.8rem 1.2rem;
    text-align: center;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    margin: 2rem 0;
    color: white;
    border: 1px solid rgba(255, 255, 255, 0.2);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
}

.welcome-title {
    font-size: 1.8rem;
    font-weight: 700;
    color: white;
    margin-bottom: 1rem;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.welcome-subtitle {
    font-size: 1.1rem;
    color: rgba(255, 255, 255, 0.9);
    margin-bottom: 1.5rem;
    line-height: 1.5;
}

.welcome-icons {
    font-size: 2.5rem;
    margin: 1.5rem 0;
    display: flex;
    justify-content: center;
    gap: 2rem;
}

.welcome-icon {
    display: inline-block;
    animation: float 3s ease-in-out infinite;
}

.welcome-icon:nth-child(2) {
    animation-delay: 0.5s;
}

.welcome-icon:nth-child(3) {
    animation-delay: 1s;
}

/* Fix for expandables and other elements */
.streamlit-expanderHeader, .stExpander {
    color: white !important;
    background-color: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
}

/* Disclaimer styling */
.disclaimer {
    font-size: 0.8rem;
    color: rgba(255, 255, 255, 0.7);
    text-align: center;
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
}

/* Summary box styling with glass effect */
.summary-box {
    background-color: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    padding: 1.5rem;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    margin-bottom: 1.5rem;
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: white;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    clear: both; /* Prevent overlap with previous elements */
}

/* Force all text elements to have white text color */
div, p, h1, h2, h3, h4, h5, h6, span, a, li, td, th {
    color: white;
}

/* Force all markdown content to have white text */
.stMarkdown div, .stMarkdown p, .stMarkdown span {
    color: white !important;
}

/* Add custom scrollbar */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.05);
}

::-webkit-scrollbar-thumb {
    background: rgba(52, 152, 219, 0.5);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: rgba(52, 152, 219, 0.8);
}

/* Completely transparent charts */
.plotly-chart-container {
    background-color: transparent !important;
    border-radius: 0 !important;
    border: none !important;
    padding: 10px !important;
    margin-top: 15px !important; /* Add margin to prevent overlap */
    position: relative; /* Ensure proper stacking context */
    z-index: 1; /* Set z-index for proper layering */
}

/* Custom animations */
@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

@keyframes float {
    0% { transform: translateY(0px); }
    50% { transform: translateY(-10px); }
    100% { transform: translateY(0px); }
}

/* Add subtle glow effect to important elements */
.metric-value, .welcome-title, .main-header {
    text-shadow: 0 0 10px rgba(52, 152, 219, 0.3);
}

/* Fix for select boxes and dropdowns */
.stSelectbox > div > div {
    background-color: rgba(255, 255, 255, 0.1) !important;
    color: white !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
}

/* Background styling for dark mode */
body {
    background-color: #1a1a2e;
    background-image: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    background-attachment: fixed;
    min-height: 100vh;
}

/* Make plots have transparent backgrounds with white text */
.js-plotly-plot .plotly .main-svg {
    background-color: transparent !important;
}

.js-plotly-plot .plotly .gtitle, 
.js-plotly-plot .plotly .xtitle, 
.js-plotly-plot .plotly .ytitle, 
.js-plotly-plot .plotly .zxtitle, 
.js-plotly-plot .plotly .zytitle {
    fill: white !important;
}

.js-plotly-plot .plotly .xtick text, 
.js-plotly-plot .plotly .ytick text, 
.js-plotly-plot .plotly .zxtick text, 
.js-plotly-plot .plotly .zytick text {
    fill: white !important;
}

.js-plotly-plot .plotly .legend text {
    fill: white !important;
}

/* Set paper and plot background to transparent */
.js-plotly-plot .plotly .plot-container .svg-container .main-svg .xyplotbg {
    fill: rgba(255, 255, 255, 0.02) !important;
}

.js-plotly-plot .plotly .bg {
    fill: transparent !important;
}

/* Fix for the overlapping boxes issue */
.stExpander {
    margin-top: 10px !important;
    margin-bottom: 10px !important;
    position: relative;
    z-index: 1;
}

/* Ensure spacing between chart elements */
.plotly-chart-container {
    clear: both; /* Prevent floating elements from overlapping */
}

/* Fix for plotly chart text visibility */
.js-plotly-plot text {
    fill: white !important;
}
</style>
""", unsafe_allow_html=True)

# Create cache directory if it doesn't exist
os.makedirs("cache", exist_ok=True)

# Create function to display sticky navigation
def display_sticky_nav():
    """Display a sticky navigation bar for easier section access."""
    st.markdown("""
    <div class="sticky-nav">
        <div class="nav-logo">
            <span>📈</span> StockInsights
        </div>
        <div class="nav-links">
            <a href="#overview" class="nav-link">Overview</a>
            <a href="#charts" class="nav-link">Charts</a>
            <a href="#technical" class="nav-link">Technical</a>
            <a href="#financials" class="nav-link">Financials</a>
            <a href="#news" class="nav-link">News</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Enhanced loading spinner
def display_loading_spinner(message="Loading data..."):
    """Display an enhanced loading spinner with message."""
    st.markdown(f"""
    <div class="loading">
        <div class="loading-spinner"></div>
        <p style="margin-top: 15px; color: rgba(255, 255, 255, 0.8);">{message}</p>
    </div>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=3600)  # Cache data for 1 hour
def get_stock_data(ticker):
    """Get stock data and cache it."""
    try:
        # Initialize the stock analyzer
        analyzer = StockAnalyzer()
        
        # Get the analysis data
        with st.spinner(f'Fetching latest data for {ticker}...'):
            display_loading_spinner(f"Analyzing {ticker}...")
            analysis = analyzer.analyze_stock(ticker)
        
        # Cache the data
        cache_file = f"cache/{ticker}_data.json"
        with open(cache_file, 'w') as f:
            json.dump(analysis, f)
        
        return analysis
    except Exception as e:
        st.error(f"Error fetching data for {ticker}: {str(e)}")
        st.error(traceback.format_exc())
        return None

def display_company_overview(data):
    """Display company overview section with improved UI."""
    st.markdown('<div class="section-header" id="overview">Company Overview</div>', unsafe_allow_html=True)
    
    if not data.get('details'):
        st.warning("Company details not available.")
        return
    
    details = data['details']
    
    # Create two columns for company info
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Company name and description in a card
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader(f"{details.get('name', 'N/A')} ({data.get('ticker', '')})")
        
        # Display badges for exchange and type
        st.markdown(
            f'<span class="badge badge-primary">{details.get("primary_exchange", "N/A")}</span> '
            f'<span class="badge badge-info">{details.get("type", "N/A")}</span>',
            unsafe_allow_html=True
        )
        
        if details.get('description'):
            st.markdown(f'<p style="margin-top: 10px; line-height: 1.6;">{details.get("description")}</p>', unsafe_allow_html=True)
        
        # Additional information
        if details.get('homepage_url'):
            st.markdown(f'<p style="margin-top: 10px;"><a href="{details.get("homepage_url")}" target="_blank" style="text-decoration: none; color: #3498db;"><span style="margin-right: 5px;">🌐</span> Company Website</a></p>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        # Create a market cap card
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        
        market_cap = details.get('market_cap')
        if market_cap:
            if market_cap >= 1_000_000_000:
                formatted_cap = f"${market_cap / 1_000_000_000:.2f}B"
            elif market_cap >= 1_000_000:
                formatted_cap = f"${market_cap / 1_000_000:.2f}M"
            else:
                formatted_cap = f"${market_cap:,.0f}"
        else:
            formatted_cap = "N/A"
        
        st.markdown(f'<div class="metric-label">Market Cap</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">{formatted_cap}</div>', unsafe_allow_html=True)
        
        # Add industry below market cap
        industry = details.get('sic_description', 'N/A')
        st.markdown(f'<div style="margin-top: 10px; font-size: 0.9rem;"><b>Industry:</b><br>{industry}</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Company details in expandable section
    with st.expander("Additional Company Details", expanded=False):
        # Create two columns
        col1, col2 = st.columns(2)
        
        # Left column data
        col1.markdown('<div class="subsection-header">General Information</div>', unsafe_allow_html=True)
        col1.markdown('<table class="styled-table"><tbody>', unsafe_allow_html=True)
        col1.markdown(f'<tr><td><strong>Exchange</strong></td><td>{details.get("primary_exchange", "N/A")}</td></tr>', unsafe_allow_html=True)
        col1.markdown(f'<tr><td><strong>Industry</strong></td><td>{details.get("sic_description", "N/A")}</td></tr>', unsafe_allow_html=True)
        col1.markdown(f'<tr><td><strong>Type</strong></td><td>{details.get("type", "N/A")}</td></tr>', unsafe_allow_html=True)
        col1.markdown('</tbody></table>', unsafe_allow_html=True)
        
        # Right column data
        col2.markdown('<div class="subsection-header">Legal Information</div>', unsafe_allow_html=True)
        col2.markdown('<table class="styled-table"><tbody>', unsafe_allow_html=True)
        col2.markdown(f'<tr><td><strong>CIK</strong></td><td>{details.get("cik", "N/A")}</td></tr>', unsafe_allow_html=True)
        col2.markdown(f'<tr><td><strong>Country</strong></td><td>{details.get("locale", "N/A")}</td></tr>', unsafe_allow_html=True)
        
        # Add address if available
        if details.get('address'):
            address = details.get('address', {})
            address_str = ', '.join(filter(None, [
                address.get('address1', ''),
                address.get('city', ''),
                address.get('state', ''),
                address.get('postal_code', '')
            ]))
            if address_str:
                col2.markdown(f'<tr><td><strong>Address</strong></td><td>{address_str}</td></tr>', unsafe_allow_html=True)
        
        col2.markdown('</tbody></table>', unsafe_allow_html=True)

def display_price_chart(data):
    """Display interactive price chart section."""
    st.markdown('<div class="section-header" id="charts">Price History</div>', unsafe_allow_html=True)
    
    if not data.get('recent_aggregates'):
        st.warning("Price data not available.")
        return
    
    # Create tabs for different chart views
    tab1, tab2 = st.tabs(["📈 Interactive Chart", "📊 Technical Chart"])
    
    with tab1:
        # Prepare data for chart
        aggs = data.get('recent_aggregates', [])
        chart_data = []
        
        for bar in aggs:
            try:
                date = datetime.fromtimestamp(bar['t'] / 1000).strftime('%Y-%m-%d')
                chart_data.append({
                    'date': date,
                    'price': float(bar['c']),
                    'open': float(bar['o']),
                    'high': float(bar['h']),
                    'low': float(bar['l']),
                    'volume': float(bar['v']),
                })
            except (KeyError, ValueError, TypeError) as e:
                continue
        
        if not chart_data:
            st.warning("Insufficient price data for visualization.")
            return
        
        # Sort by date
        chart_data = sorted(chart_data, key=lambda x: x['date'])
        
        # Create Plotly figure
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                          row_heights=[0.7, 0.3],
                          subplot_titles=("Price", "Volume"),
                          vertical_spacing=0.1)
        
        # Add price line
        fig.add_trace(
            go.Scatter(
                x=[item['date'] for item in chart_data],
                y=[item['price'] for item in chart_data],
                mode='lines',
                name='Price',
                line=dict(color=COLOR_PRIMARY, width=2),
                hovertemplate='%{x}<br>Price: $%{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )
        
        # Add area fill below price line for better visualization
        fig.add_trace(
            go.Scatter(
                x=[item['date'] for item in chart_data],
                y=[item['price'] for item in chart_data],
                mode='none',
                name='Price Area',
                fill='tozeroy',
                fillcolor=f'rgba(52, 152, 219, 0.2)',
                hoverinfo='skip'
            ),
            row=1, col=1
        )
        
        # Add SMA if available
        if data.get('sma_50') and data['sma_50'].get('values'):
            sma_data = []
            for point in data['sma_50']['values']:
                try:
                    date = datetime.fromtimestamp(point['timestamp'] / 1000).strftime('%Y-%m-%d')
                    # Only include points within our date range
                    if date in [item['date'] for item in chart_data]:
                        sma_data.append({
                            'date': date,
                            'value': float(point['value'])
                        })
                except (KeyError, ValueError, TypeError):
                    continue
            
            # Sort by date
            sma_data = sorted(sma_data, key=lambda x: x['date'])
            
            if sma_data:
                fig.add_trace(
                    go.Scatter(
                        x=[item['date'] for item in sma_data],
                        y=[item['value'] for item in sma_data],
                        mode='lines',
                        name='50-day SMA',
                        line=dict(color=COLOR_WARNING, width=2, dash='dash'),
                        hovertemplate='%{x}<br>SMA: $%{y:.2f}<extra></extra>'
                    ),
                    row=1, col=1
                )
        
        # Add volume bars with color coding
        colors = []
        for i in range(1, len(chart_data)):
            if chart_data[i]['price'] >= chart_data[i-1]['price']:
                colors.append(COLOR_POSITIVE)  # Green for up days
            else:
                colors.append(COLOR_NEGATIVE)  # Red for down days
        
        # Add first day color
        if colors:
            colors.insert(0, COLOR_NEUTRAL)  # Gray for first day
        else:
            colors = [COLOR_NEUTRAL] * len(chart_data)
        
        fig.add_trace(
            go.Bar(
                x=[item['date'] for item in chart_data],
                y=[item['volume'] for item in chart_data],
                marker=dict(color=colors),
                name='Volume',
                hovertemplate='%{x}<br>Volume: %{y:,.0f}<extra></extra>'
            ),
            row=2, col=1
        )
        
        # Add annotations for highest and lowest prices
        if chart_data:
            highest_price = max(chart_data, key=lambda x: x['price'])
            lowest_price = min(chart_data, key=lambda x: x['price'])
            
            fig.add_annotation(
                x=highest_price['date'],
                y=highest_price['price'],
                text=f"High: ${highest_price['price']:.2f}",
                showarrow=True,
                arrowhead=2,
                arrowcolor=COLOR_POSITIVE,
                arrowsize=1,
                arrowwidth=2,
                ax=0,
                ay=-40,
                font=dict(size=12, color="white"),
                bgcolor="rgba(39, 174, 96, 0.7)",
                bordercolor=COLOR_POSITIVE,
                borderwidth=1,
                borderpad=4,
                align="center"
            )
            
            fig.add_annotation(
                x=lowest_price['date'],
                y=lowest_price['price'],
                text=f"Low: ${lowest_price['price']:.2f}",
                showarrow=True,
                arrowhead=2,
                arrowcolor=COLOR_NEGATIVE,
                arrowsize=1,
                arrowwidth=2,
                ax=0,
                ay=40,
                font=dict(size=12, color="white"),
                bgcolor="rgba(231, 76, 60, 0.7)",
                bordercolor=COLOR_NEGATIVE,
                borderwidth=1,
                borderpad=4,
                align="center"
            )
        
        # Update layout
        fig.update_layout(
            height=600,
            title=f"{data.get('ticker', 'Stock')} - Price History (Last 30 Days)",
            title_font=dict(size=20, color="white"),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor="rgba(0, 0, 0, 0.5)",
                bordercolor=COLOR_PRIMARY,
                borderwidth=1,
                font=dict(color="white")
            ),
            margin=dict(l=0, r=0, t=60, b=0),
            hovermode="x unified",
            hoverlabel=dict(
                bgcolor="rgba(0, 0, 0, 0.7)",
                font_size=12,
                font_family="Arial",
                font_color="white"
            ),
            xaxis=dict(
                gridcolor="rgba(255, 255, 255, 0.1)",
                title_font=dict(size=14, color="white"),
                tickfont=dict(color="white")
            ),
            yaxis=dict(
                gridcolor="rgba(255, 255, 255, 0.1)",
                title_font=dict(size=14, color="white"),
                tickprefix="$",
                tickfont=dict(color="white")
            ),
            xaxis2=dict(
                gridcolor="rgba(255, 255, 255, 0.1)",
                rangeslider=dict(visible=True),
                type="category",
                title_font=dict(size=14, color="white"),
                tickfont=dict(color="white")
            ),
            yaxis2=dict(
                gridcolor="rgba(255, 255, 255, 0.1)",
                title_font=dict(size=14, color="white"),
                tickfont=dict(color="white")
            ),
            plot_bgcolor="rgba(0, 0, 0, 0.2)",
            paper_bgcolor="rgba(0, 0, 0, 0.2)",
        )
        
        # Display the chart
        st.plotly_chart(fig, use_container_width=True)
        
        # Add price statistics cards
        if chart_data:
            st.markdown('<div class="subsection-header">Price Statistics</div>', unsafe_allow_html=True)
            
            # Create key metrics
            current_price = chart_data[-1]['price']
            price_change = chart_data[-1]['price'] - chart_data[0]['price']
            price_change_pct = (price_change / chart_data[0]['price']) * 100
            highest_price = max([item['price'] for item in chart_data])
            lowest_price = min([item['price'] for item in chart_data])
            avg_volume = sum([item['volume'] for item in chart_data]) / len(chart_data)
            
            # Display metrics in columns
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.markdown('<div class="metric-label">Current Price</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-value">${current_price:.2f}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.markdown('<div class="metric-label">30-Day Change</div>', unsafe_allow_html=True)
                
                if price_change >= 0:
                    st.markdown(f'<div class="metric-value positive">+${price_change:.2f} <small>(+{price_change_pct:.2f}%)</small></div>', 
                               unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="metric-value negative">-${abs(price_change):.2f} <small>({price_change_pct:.2f}%)</small></div>', 
                               unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col3:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.markdown('<div class="metric-label">Price Range (30d)</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-value">${lowest_price:.2f} - ${highest_price:.2f}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col4:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.markdown('<div class="metric-label">Avg. Volume</div>', unsafe_allow_html=True)
                
                if avg_volume >= 1_000_000:
                    formatted_volume = f"{avg_volume/1_000_000:.2f}M"
                elif avg_volume >= 1_000:
                    formatted_volume = f"{avg_volume/1_000:.1f}K"
                else:
                    formatted_volume = f"{avg_volume:.0f}"
                
                st.markdown(f'<div class="metric-value">{formatted_volume}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        # Create candlestick chart
        fig = go.Figure(data=[go.Candlestick(
            x=[item['date'] for item in chart_data],
            open=[item['open'] for item in chart_data], 
            high=[item['high'] for item in chart_data],
            low=[item['low'] for item in chart_data], 
            close=[item['price'] for item in chart_data],
            increasing=dict(line=dict(color=COLOR_POSITIVE), fillcolor=COLOR_POSITIVE),
            decreasing=dict(line=dict(color=COLOR_NEGATIVE), fillcolor=COLOR_NEGATIVE),
            name='OHLC'
        )])
        
        # Add SMA if available
        if data.get('sma_50') and data['sma_50'].get('values'):
            sma_data = []
            for point in data['sma_50']['values']:
                try:
                    date = datetime.fromtimestamp(point['timestamp'] / 1000).strftime('%Y-%m-%d')
                    # Only include points within our date range
                    if date in [item['date'] for item in chart_data]:
                        sma_data.append({
                            'date': date,
                            'value': float(point['value'])
                        })
                except (KeyError, ValueError, TypeError):
                    continue
            
            # Sort by date
            sma_data = sorted(sma_data, key=lambda x: x['date'])
            
            if sma_data:
                fig.add_trace(
                    go.Scatter(
                        x=[item['date'] for item in sma_data],
                        y=[item['value'] for item in sma_data],
                        mode='lines',
                        name='50-day SMA',
                        line=dict(color='#8E44AD', width=2)
                    )
                )
        
        # Update layout
        fig.update_layout(
            title=f"{data.get('ticker', 'Stock')} - OHLC Chart",
            title_font=dict(size=20, color="white"),
            yaxis_title='Price ($)',
            xaxis_title='Date',
            height=600,
            margin=dict(l=0, r=0, t=60, b=0),
            hovermode="x unified",
            hoverlabel=dict(
                bgcolor="rgba(0, 0, 0, 0.7)",
                font_size=12,
                font_family="Arial",
                font_color="white"
            ),
            xaxis=dict(
                rangeslider=dict(visible=True),
                type="category",
                gridcolor="rgba(255, 255, 255, 0.1)",
                tickfont=dict(color="white")
            ),
            yaxis=dict(
                gridcolor="rgba(255, 255, 255, 0.1)",
                tickprefix="$",
                tickfont=dict(color="white")
            ),
            plot_bgcolor="rgba(0, 0, 0, 0.2)",
            paper_bgcolor="rgba(0, 0, 0, 0.2)",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor="rgba(0, 0, 0, 0.5)",
                bordercolor=COLOR_PRIMARY,
                borderwidth=1,
                font=dict(color="white")
            ),
        )
        
        st.plotly_chart(fig, use_container_width=True)

def calculate_rsi(prices, window=14):
    """Calculate Relative Strength Index."""
    try:
        if len(prices) < window + 1:
            return None
        
        # Calculate price changes
        delta = np.diff(prices)
        
        # Create arrays for gains and losses
        gains = np.zeros_like(delta)
        losses = np.zeros_like(delta)
        
        # Separate gains and losses
        gains[delta > 0] = delta[delta > 0]
        losses[delta < 0] = -delta[delta < 0]  # Convert to positive values
        
        # Calculate average gains and losses
        avg_gain = np.mean(gains[:window])
        avg_loss = np.mean(losses[:window])
        
        # Initialize RSI list
        rsi = []
        
        # Calculate first RSI value
        if avg_loss == 0:
            rsi.append(100)
        else:
            rs = avg_gain / avg_loss
            rsi.append(100 - (100 / (1 + rs)))
        
        # Calculate smoothed RSI for remaining points
        for i in range(window, len(delta)):
            avg_gain = (avg_gain * (window - 1) + gains[i]) / window
            avg_loss = (avg_loss * (window - 1) + losses[i]) / window
            
            if avg_loss == 0:
                rsi.append(100)
            else:
                rs = avg_gain / avg_loss
                rsi.append(100 - (100 / (1 + rs)))
        
        return rsi
    except Exception as e:
        st.error(f"Error calculating RSI: {str(e)}")
        return None

def display_technical_analysis(data):
    """Display technical analysis section."""
    st.markdown('<div class="section-header" id="technical">Technical Analysis</div>', unsafe_allow_html=True)
    
    if not data.get('recent_aggregates'):
        st.markdown('<div class="warning-box">Insufficient data for technical analysis.</div>', unsafe_allow_html=True)
        return
    
    # Extract price data
    aggs = data.get('recent_aggregates', [])
    
    # Calculate RSI if we have enough data
    rsi_value = None
    if len(aggs) >= 14:
        prices = []
        for bar in aggs:
            try:
                prices.append(float(bar['c']))
            except (KeyError, ValueError, TypeError):
                continue
        
        if len(prices) >= 14:
            rsi_value = calculate_rsi(prices, 14)[-1] if calculate_rsi(prices, 14) else None
    
    # Get SMA value
    sma_value = None
    if data.get('sma_50') and data['sma_50'].get('values'):
        try:
            sma_value = float(data['sma_50']['values'][-1]['value'])
        except (IndexError, KeyError, ValueError, TypeError):
            pass
    
    # Get latest price
    latest_price = None
    if aggs:
        try:
            latest_price = float(aggs[-1]['c'])
        except (KeyError, ValueError, TypeError):
            pass
    
    # Display technical indicators in enhanced cards
    col1, col2, col3 = st.columns(3)
    
    # 50-day SMA card
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">50-day SMA</div>', unsafe_allow_html=True)
        
        if latest_price is not None and sma_value is not None:
            st.markdown(f'<div class="metric-value">${sma_value:.2f}</div>', unsafe_allow_html=True)
            
            # Add signal with icon
            if latest_price > sma_value:
                st.markdown('<div class="badge badge-success"><span style="margin-right: 5px;">▲</span> BULLISH</div>', unsafe_allow_html=True)
                st.markdown('<div style="font-size: 0.9rem; margin-top: 8px;">Price > SMA</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="badge badge-danger"><span style="margin-right: 5px;">▼</span> BEARISH</div>', unsafe_allow_html=True)
                st.markdown('<div style="font-size: 0.9rem; margin-top: 8px;">Price < SMA</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="metric-value">N/A</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # RSI card
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">RSI (14-day)</div>', unsafe_allow_html=True)
        
        if rsi_value is not None:
            # Add gauge-like visualization
            if rsi_value < 30:
                color_style = "success"
                signal_text = "OVERSOLD"
                icon = "▲"
                gauge_pct = (rsi_value / 30) * 100
            elif rsi_value > 70:
                color_style = "danger"
                signal_text = "OVERBOUGHT"
                icon = "▼"
                gauge_pct = ((rsi_value - 70) / 30) * 100
            else:
                color_style = "primary"
                signal_text = "NEUTRAL"
                icon = "■"
                gauge_pct = ((rsi_value - 30) / 40) * 100
            
            # Limit gauge percentage to 0-100
            gauge_pct = max(0, min(100, gauge_pct))
            
            st.markdown(f'<div class="metric-value">{rsi_value:.2f}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="badge badge-{color_style}"><span style="margin-right: 5px;">{icon}</span> {signal_text}</div>', unsafe_allow_html=True)
            
            # Add mini gauge bar
            st.markdown(f'''
            <div style="margin-top: 8px; width: 100%; height: 8px; background-color: rgba(255, 255, 255, 0.1); border-radius: 4px; overflow: hidden;">
                <div style="width: {gauge_pct}%; height: 100%; background-color: {COLOR_PRIMARY};"></div>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 0.7rem; margin-top: 2px;">
                <span>0</span>
                <span>30</span>
                <span>70</span>
                <span>100</span>
            </div>
            ''', unsafe_allow_html=True)
        else:
            st.markdown('<div class="metric-value">N/A</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Price vs SMA card
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Current Price</div>', unsafe_allow_html=True)
        
        if latest_price is not None:
            st.markdown(f'<div class="metric-value">${latest_price:.2f}</div>', unsafe_allow_html=True)
            
            # Add comparison to SMA
            if sma_value is not None:
                diff_pct = ((latest_price - sma_value) / sma_value) * 100
                if diff_pct >= 0:
                    st.markdown(f'<div style="color: {COLOR_POSITIVE}; font-weight: bold; margin-top: 8px;">{diff_pct:.2f}% above SMA</div>', unsafe_allow_html=True)
                    
                    # Add mini chart-like visualization
                    st.markdown(f'''
                    <div style="display: flex; align-items: center; margin-top: 5px;">
                        <div style="background-color: {COLOR_NEUTRAL}; height: 2px; width: 40%;"></div>
                        <div style="border-left: 5px solid {COLOR_POSITIVE}; height: 10px;"></div>
                        <div style="background-color: {COLOR_NEUTRAL}; height: 2px; width: 40%;"></div>
                    </div>
                    ''', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div style="color: {COLOR_NEGATIVE}; font-weight: bold; margin-top: 8px;">{abs(diff_pct):.2f}% below SMA</div>', unsafe_allow_html=True)
                    
                    # Add mini chart-like visualization
                    st.markdown(f'''
                    <div style="display: flex; align-items: center; margin-top: 5px;">
                        <div style="background-color: {COLOR_NEUTRAL}; height: 2px; width: 40%;"></div>
                        <div style="border-left: 5px solid {COLOR_NEGATIVE}; height: 10px;"></div>
                        <div style="background-color: {COLOR_NEUTRAL}; height: 2px; width: 40%;"></div>
                    </div>
                    ''', unsafe_allow_html=True)
        else:
            st.markdown('<div class="metric-value">N/A</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Add overall signal
    if latest_price is not None and (sma_value is not None or rsi_value is not None):
        # Count bullish vs bearish signals
        bullish_signals = 0
        bearish_signals = 0
        total_signals = 0
        
        if latest_price is not None and sma_value is not None:
            total_signals += 1
            if latest_price > sma_value:
                bullish_signals += 1
            else:
                bearish_signals += 1
        
        if rsi_value is not None:
            total_signals += 1
            if rsi_value < 30:
                bullish_signals += 1
            elif rsi_value > 70:
                bearish_signals += 1
            elif rsi_value > 50:
                bullish_signals += 0.5
                bearish_signals += 0.5
            else:
                bearish_signals += 0.5
                bullish_signals += 0.5
        
        # Create signal card
        signal_text = ""
        signal_class = ""
        
        if total_signals > 0:
            bullish_pct = (bullish_signals / total_signals) * 100
            
            if bullish_pct >= 70:
                signal_text = "BULLISH"
                signal_class = "success-box"
                signal_icon = "▲"
            elif bullish_pct <= 30:
                signal_text = "BEARISH"
                signal_class = "error-box"
                signal_icon = "▼"
            else:
                signal_text = "NEUTRAL"
                signal_class = "info-box"
                signal_icon = "■"
            
            st.markdown(f'<div class="{signal_class}" style="margin-top: 20px; text-align: center;">', unsafe_allow_html=True)
            st.markdown(f'<h3 style="margin-bottom: 10px;">Overall Signal: <span style="margin-right: 5px;">{signal_icon}</span> {signal_text}</h3>', unsafe_allow_html=True)
            
            # Add signal strength meter
            if signal_text == "NEUTRAL":
                st.markdown('''
                <div style="display: flex; justify-content: space-between; align-items: center; margin: 10px 0;">
                    <div style="text-align: center; width: 30%;">
                        <div style="font-weight: bold; color: #e74c3c;">Bearish</div>
                    </div>
                    <div style="text-align: center; width: 30%;">
                        <div style="font-weight: bold; color: #3498db; border: 2px solid #3498db; border-radius: 20px; padding: 5px;">Neutral</div>
                    </div>
                    <div style="text-align: center; width: 30%;">
                        <div style="font-weight: bold; color: #27ae60;">Bullish</div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            elif signal_text == "BULLISH":
                st.markdown('''
                <div style="display: flex; justify-content: space-between; align-items: center; margin: 10px 0;">
                    <div style="text-align: center; width: 30%;">
                        <div style="font-weight: bold; color: #e74c3c;">Bearish</div>
                    </div>
                    <div style="text-align: center; width: 30%;">
                        <div style="font-weight: bold; color: #3498db;">Neutral</div>
                    </div>
                    <div style="text-align: center; width: 30%;">
                        <div style="font-weight: bold; color: #27ae60; border: 2px solid #27ae60; border-radius: 20px; padding: 5px;">Bullish</div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            else:  # BEARISH
                st.markdown('''
                <div style="display: flex; justify-content: space-between; align-items: center; margin: 10px 0;">
                    <div style="text-align: center; width: 30%;">
                        <div style="font-weight: bold; color: #e74c3c; border: 2px solid #e74c3c; border-radius: 20px; padding: 5px;">Bearish</div>
                    </div>
                    <div style="text-align: center; width: 30%;">
                        <div style="font-weight: bold; color: #3498db;">Neutral</div>
                    </div>
                    <div style="text-align: center; width: 30%;">
                        <div style="font-weight: bold; color: #27ae60;">Bullish</div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Add technical commentary
    if latest_price is not None and (sma_value is not None or rsi_value is not None):
        st.markdown('<div class="subsection-header">Technical Commentary</div>', unsafe_allow_html=True)
        
        commentary = []
        
        # Price vs SMA commentary
        if latest_price is not None and sma_value is not None:
            diff_pct = ((latest_price - sma_value) / sma_value) * 100
            if latest_price > sma_value:
                if diff_pct > 10:
                    commentary.append(f"The stock is trading significantly above its 50-day SMA (${sma_value:.2f}), with the current price (${latest_price:.2f}) being {diff_pct:.2f}% higher. This indicates a strong bullish trend, though the stock may be approaching overbought territory.")
                elif diff_pct > 5:
                    commentary.append(f"The stock is trading moderately above its 50-day SMA (${sma_value:.2f}), with the current price (${latest_price:.2f}) being {diff_pct:.2f}% higher. This suggests a healthy bullish trend that may continue in the near term.")
                else:
                    commentary.append(f"The stock is trading slightly above its 50-day SMA (${sma_value:.2f}), with the current price (${latest_price:.2f}) being {diff_pct:.2f}% higher. This indicates a mild bullish trend, though momentum should be monitored.")
            else:
                diff_pct = abs(diff_pct)
                if diff_pct > 10:
                    commentary.append(f"The stock is trading significantly below its 50-day SMA (${sma_value:.2f}), with the current price (${latest_price:.2f}) being {diff_pct:.2f}% lower. This indicates a strong bearish trend, though the stock may be approaching oversold territory.")
                elif diff_pct > 5:
                    commentary.append(f"The stock is trading moderately below its 50-day SMA (${sma_value:.2f}), with the current price (${latest_price:.2f}) being {diff_pct:.2f}% lower. This suggests a bearish trend that may continue in the near term.")
                else:
                    commentary.append(f"The stock is trading slightly below its 50-day SMA (${sma_value:.2f}), with the current price (${latest_price:.2f}) being {diff_pct:.2f}% lower. This indicates a mild bearish trend, though a reversal could occur with positive catalysts.")
        
        # RSI commentary
        if rsi_value is not None:
            if rsi_value < 30:
                if rsi_value < 20:
                    commentary.append(f"The RSI reading of {rsi_value:.2f} indicates the stock is extremely oversold. This often precedes a strong price reversal to the upside, presenting a potential buying opportunity for contrarian investors.")
                else:
                    commentary.append(f"The RSI reading of {rsi_value:.2f} indicates the stock is oversold. This may present a buying opportunity, as oversold conditions often precede price reversals to the upside.")
            elif rsi_value > 70:
                if rsi_value > 80:
                    commentary.append(f"The RSI reading of {rsi_value:.2f} indicates the stock is extremely overbought. This often precedes a price correction, suggesting caution for new buyers and potential profit-taking for current holders.")
                else:
                    commentary.append(f"The RSI reading of {rsi_value:.2f} indicates the stock is overbought. This suggests caution for new buyers, as overbought conditions often precede price reversals to the downside.")
            elif rsi_value > 60:
                commentary.append(f"The RSI reading of {rsi_value:.2f} is in the upper neutral range, leaning bullish. While not overbought, the momentum is positive, supporting the current price trend.")
            elif rsi_value < 40:
                commentary.append(f"The RSI reading of {rsi_value:.2f} is in the lower neutral range, leaning bearish. While not oversold, the momentum is negative, which may put pressure on prices.")
            else:
                commentary.append(f"The RSI reading of {rsi_value:.2f} is in the neutral range, suggesting balanced buying and selling pressure. The indicator provides no strong directional signal at this time.")
        
        # Display commentary
        if commentary:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("<br>".join(commentary), unsafe_allow_html=True)
            
            # Add conclusions if we have multiple signals
            if len(commentary) >= 2:
                # Overall signal strength
                bullish = 0
                bearish = 0
                
                if latest_price is not None and sma_value is not None:
                    if latest_price > sma_value:
                        bullish += 1
                    else:
                        bearish += 1
                
                if rsi_value is not None:
                    if rsi_value < 30:
                        bullish += 1
                    elif rsi_value > 70:
                        bearish += 1
                    elif rsi_value > 50:
                        bullish += 0.5
                    else:
                        bearish += 0.5
                
                # Generate conclusion
                st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)
                
                if bullish > bearish:
                    st.markdown(f"<p style='font-weight: bold;'><span style='color: {COLOR_POSITIVE};'>▲</span> <u>Conclusion:</u> Technical indicators are leaning bullish. This suggests upward price movements may be more likely in the near term, though investors should monitor for any shift in momentum.</p>", unsafe_allow_html=True)
                elif bearish > bullish:
                    st.markdown(f"<p style='font-weight: bold;'><span style='color: {COLOR_NEGATIVE};'>▼</span> <u>Conclusion:</u> Technical indicators are leaning bearish. This suggests downward price movements may be more likely in the near term, though investors should watch for potential reversals.</p>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<p style='font-weight: bold;'><span style='color: {COLOR_NEUTRAL};'>■</span> <u>Conclusion:</u> Technical indicators are mixed, showing no clear directional bias. In such cases, it's advisable to wait for more definitive signals before making significant trading decisions.</p>", unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Add RSI chart if we have data
    if rsi_value is not None:
        st.markdown('<div class="subsection-header">RSI Chart (14-day)</div>', unsafe_allow_html=True)
        
        # Calculate full RSI series
        prices = []
        dates = []
        for bar in aggs:
            try:
                date = datetime.fromtimestamp(bar['t'] / 1000).strftime('%Y-%m-%d')
                price = float(bar['c'])
                prices.append(price)
                dates.append(date)
            except (KeyError, ValueError, TypeError):
                continue
        
        if len(prices) >= 14:
            rsi_values = calculate_rsi(prices, 14)
            
            # Only take dates that correspond to the RSI values (which start from the 14th day)
            rsi_dates = dates[13:]
            
            if len(rsi_dates) == len(rsi_values):
                # Create RSI chart
                fig = go.Figure()
                
                # Add RSI line
                fig.add_trace(go.Scatter(
                    x=rsi_dates,
                    y=rsi_values,
                    mode='lines',
                    name='RSI',
                    line=dict(color=COLOR_PRIMARY, width=2)
                ))
                
                # Add shaded areas for overbought and oversold
                # Overbought area (above 70)
                fig.add_trace(go.Scatter(
                    x=rsi_dates,
                    y=[70] * len(rsi_dates),
                    fill=None,
                    mode='lines',
                    line=dict(color='rgba(0,0,0,0)'),
                    showlegend=False
                ))
                
                fig.add_trace(go.Scatter(
                    x=rsi_dates,
                    y=[100] * len(rsi_dates),
                    fill='tonexty',
                    mode='lines',
                    line=dict(color='rgba(0,0,0,0)'),
                    fillcolor=f'rgba({COLOR_NEGATIVE.replace("rgb", "").replace("(", "").replace(")", "")}, 0.2)',
                    showlegend=False
                ))
                
                # Oversold area (below 30)
                fig.add_trace(go.Scatter(
                    x=rsi_dates,
                    y=[0] * len(rsi_dates),
                    fill=None,
                    mode='lines',
                    line=dict(color='rgba(0,0,0,0)'),
                    showlegend=False
                ))
                
                fig.add_trace(go.Scatter(
                    x=rsi_dates,
                    y=[30] * len(rsi_dates),
                    fill='tonexty',
                    mode='lines',
                    line=dict(color='rgba(0,0,0,0)'),
                    fillcolor=f'rgba({COLOR_POSITIVE.replace("rgb", "").replace("(", "").replace(")", "")}, 0.2)',
                    showlegend=False
                ))
                
                # Add overbought and oversold lines
                fig.add_shape(
                    type="line",
                    x0=rsi_dates[0],
                    y0=70,
                    x1=rsi_dates[-1],
                    y1=70,
                    line=dict(color=COLOR_NEGATIVE, width=2, dash="dash"),
                )
                
                fig.add_shape(
                    type="line",
                    x0=rsi_dates[0],
                    y0=30,
                    x1=rsi_dates[-1],
                    y1=30,
                    line=dict(color=COLOR_POSITIVE, width=2, dash="dash"),
                )
                
                # Add annotations
                fig.add_annotation(
                    x=rsi_dates[0],
                    y=70,
                    text="Overbought",
                    showarrow=False,
                    yshift=10,
                    font=dict(color=COLOR_NEGATIVE)
                )
                
                fig.add_annotation(
                    x=rsi_dates[0],
                    y=30,
                    text="Oversold",
                    showarrow=False,
                    yshift=-10,
                    font=dict(color=COLOR_POSITIVE)
                )
                
                # Update layout
                fig.update_layout(
                    title="RSI (14-day)",
                    title_font=dict(size=20, color="white"),
                    xaxis_title="Date",
                    yaxis_title="RSI",
                    height=400,
                    yaxis=dict(
                        range=[0, 100],
                        gridcolor="rgba(255, 255, 255, 0.1)",
                        tickfont=dict(color="white")
                    ),
                    xaxis=dict(
                        type="category",
                        gridcolor="rgba(255, 255, 255, 0.1)",
                        tickfont=dict(color="white")
                    ),
                    margin=dict(l=0, r=0, t=60, b=0),
                    plot_bgcolor="rgba(0, 0, 0, 0.2)",
                    paper_bgcolor="rgba(0, 0, 0, 0.2)",
                    hovermode="x unified",
                    font=dict(color="white")
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Add RSI interpretation
                st.markdown('<div class="info-box">', unsafe_allow_html=True)
                st.markdown("""
                <p><strong>Understanding RSI:</strong></p>
                <ul>
                    <li><strong>Values above 70</strong> indicate the stock may be <strong style="color: #e74c3c;">overbought</strong> and could be due for a price correction.</li>
                    <li><strong>Values below 30</strong> indicate the stock may be <strong style="color: #27ae60;">oversold</strong> and could present a buying opportunity.</li>
                    <li><strong>Values between 30-70</strong> indicate neutral momentum conditions.</li>
                </ul>
                """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

def extract_financial_metrics(report):
    """Extract key financial metrics from a report."""
    try:
        metrics = {}
        
        # Try to extract common financial metrics
        metric_mapping = {
            "revenues": "Revenue",
            "net_income": "Net Income",
            "eps_basic": "EPS",
            "assets": "Total Assets",
            "liabilities": "Total Liabilities",
            "cash_and_equivalents": "Cash & Equivalents"
        }
        
        # Financial data might be nested in different ways
        financials = report.get('financials', {})
        
        for statement in ['income_statement', 'balance_sheet', 'cash_flow_statement']:
            if statement in financials:
                for metric_key, metric_name in metric_mapping.items():
                    if metric_key in financials[statement]:
                        value = financials[statement][metric_key]
                        
                        # Handle different value types
                        if isinstance(value, dict):
                            # Try common keys that might contain the actual value
                            for key in ['value', 'amount', 'total', 'raw']:
                                if key in value and isinstance(value[key], (int, float)):
                                    value = value[key]
                                    break
                            
                            # If still a dict, try to get the first numeric value
                            if isinstance(value, dict):
                                for val in value.values():
                                    if isinstance(val, (int, float)):
                                        value = val
                                        break
                        
                        # Format the value
                        if isinstance(value, (int, float)):
                            if abs(value) >= 1_000_000_000:
                                metrics[metric_name] = f"${value / 1_000_000_000:.2f}B"
                            elif abs(value) >= 1_000_000:
                                metrics[metric_name] = f"${value / 1_000_000:.2f}M"
                            elif abs(value) >= 1_000:
                                metrics[metric_name] = f"${value / 1_000:.2f}K"
                            else:
                                metrics[metric_name] = f"${value:.2f}"
                        else:
                            metrics[metric_name] = "N/A"
        
        return metrics
    except Exception as e:
        st.error(f"Error extracting financial metrics: {str(e)}")
        return {}

def parse_financial_value(value_str):
    """Parse a financial value string and return the numeric value."""
    try:
        if value_str == 'N/A':
            return None
        
        # Strip any currency symbols and commas
        cleaned = value_str.replace('$', '').replace(',', '')
        
        # Handle B/M/K suffixes
        if 'B' in cleaned:
            return float(cleaned.replace('B', '')) * 1_000_000_000
        elif 'M' in cleaned:
            return float(cleaned.replace('M', '')) * 1_000_000
        elif 'K' in cleaned:
            return float(cleaned.replace('K', '')) * 1_000
        else:
            return float(cleaned)
    except (ValueError, AttributeError, TypeError):
        return None

def display_financial_highlights(data):
    """Display financial highlights section."""
    st.markdown('<div class="section-header" id="financials">Financial Highlights</div>', unsafe_allow_html=True)
    
    # Check if financial data is available
    if not data.get('financials'):
        st.markdown('<div class="warning-box">No financial data available.</div>', unsafe_allow_html=True)
        return
    
    financials = data.get('financials', [])
    
    if not financials:
        st.markdown('<div class="warning-box">Financial data not available.</div>', unsafe_allow_html=True)
        return
    
    # Get the latest financial report
    latest_report = financials[0] if financials else None
    
    if not latest_report:
        st.markdown('<div class="warning-box">No financial reports available.</div>', unsafe_allow_html=True)
        return
    
    report_date = latest_report.get('filing_date', 'N/A')
    st.markdown(f'<p style="font-size: 1.1rem; margin-bottom: 20px;">Latest financial data as of: <span style="font-weight: bold;">{report_date}</span></p>', unsafe_allow_html=True)
    
    # Create tabs for different financial views
    tab1, tab2 = st.tabs(["📊 Key Metrics", "📑 SEC Filings"])
    
    with tab1:
        # Extract key financial metrics
        metrics = extract_financial_metrics(latest_report)
        
        if not metrics:
            st.markdown('<div class="warning-box">Could not extract detailed financial metrics.</div>', unsafe_allow_html=True)
            return
        
        # Display metrics in cards
        st.markdown('<div class="subsection-header">Financial Metrics</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Revenue</div>', unsafe_allow_html=True)
            if 'Revenue' in metrics:
                st.markdown(f'<div class="metric-value">{metrics["Revenue"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="metric-value">N/A</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Net Income</div>', unsafe_allow_html=True)
            if 'Net Income' in metrics:
                net_income_value = parse_financial_value(metrics["Net Income"])
                net_income_class = "positive" if net_income_value and net_income_value > 0 else "negative"
                st.markdown(f'<div class="metric-value {net_income_class}">{metrics["Net Income"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="metric-value">N/A</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">EPS</div>', unsafe_allow_html=True)
            if 'EPS' in metrics:
                eps_value = parse_financial_value(metrics["EPS"])
                eps_class = "positive" if eps_value and eps_value > 0 else "negative"
                st.markdown(f'<div class="metric-value {eps_class}">{metrics["EPS"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="metric-value">N/A</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Total Assets</div>', unsafe_allow_html=True)
            if 'Total Assets' in metrics:
                st.markdown(f'<div class="metric-value">{metrics["Total Assets"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="metric-value">N/A</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Total Liabilities</div>', unsafe_allow_html=True)
            if 'Total Liabilities' in metrics:
                st.markdown(f'<div class="metric-value">{metrics["Total Liabilities"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="metric-value">N/A</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Cash & Equivalents</div>', unsafe_allow_html=True)
            if 'Cash & Equivalents' in metrics:
                st.markdown(f'<div class="metric-value">{metrics["Cash & Equivalents"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="metric-value">N/A</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Financial health assessment
        st.markdown('<div class="subsection-header">Financial Health Assessment</div>', unsafe_allow_html=True)
        
        # Parse numeric values from metrics
        revenue = parse_financial_value(metrics.get('Revenue', 'N/A'))
        net_income = parse_financial_value(metrics.get('Net Income', 'N/A'))
        assets = parse_financial_value(metrics.get('Total Assets', 'N/A'))
        liabilities = parse_financial_value(metrics.get('Total Liabilities', 'N/A'))
        
        assessment_points = []
        
        # Profitability assessment
        if isinstance(revenue, (int, float)) and isinstance(net_income, (int, float)) and revenue > 0:
            profit_margin = (net_income / revenue) * 100
            
            # Create profitability card
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div style="display: flex; justify-content: space-between; align-items: center;">', unsafe_allow_html=True)
            st.markdown(f'<h3 style="margin: 0;">Profitability</h3>', unsafe_allow_html=True)
            
            # Profit margin gauge
            if profit_margin > 15:
                gauge_color = COLOR_POSITIVE
                rating = "Excellent"
            elif profit_margin > 10:
                gauge_color = "#2ecc71"  # Lighter green
                rating = "Good"
            elif profit_margin > 5:
                gauge_color = "#f1c40f"  # Yellow
                rating = "Moderate"
            elif profit_margin > 0:
                gauge_color = "#e67e22"  # Orange
                rating = "Low"
            else:
                gauge_color = COLOR_NEGATIVE
                rating = "Concerning"
            
            st.markdown(f'<span class="badge" style="background-color: {gauge_color}; color: white;">{rating}</span>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Profit margin details
            st.markdown(f'<p>Profit Margin: <strong>{profit_margin:.2f}%</strong></p>', unsafe_allow_html=True)
            
            # Add gauge visualization
            gauge_pct = min(100, max(0, profit_margin * 4))  # Scale to make 25% profit margin = 100% of gauge
            st.markdown(f'''
            <div style="margin: 10px 0; width: 100%; height: 10px; background-color: rgba(255, 255, 255, 0.1); border-radius: 5px; overflow: hidden;">
                <div style="width: {gauge_pct}%; height: 100%; background-color: {gauge_color};"></div>
            </div>
            ''', unsafe_allow_html=True)
            
            # Add interpretation
            if profit_margin > 15:
                st.markdown('<p>The company demonstrates strong profitability, well above industry averages.</p>', unsafe_allow_html=True)
            elif profit_margin > 10:
                st.markdown('<p>The company shows healthy profitability.</p>', unsafe_allow_html=True)
            elif profit_margin > 5:
                st.markdown('<p>The profit margin is acceptable but leaves room for improvement.</p>', unsafe_allow_html=True)
            elif profit_margin > 0:
                st.markdown('<p>The profit margin indicates minimal profitability.</p>', unsafe_allow_html=True)
            else:
                st.markdown('<p>The company is operating at a loss, which may be concerning for investors.</p>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Balance sheet health
        if isinstance(assets, (int, float)) and isinstance(liabilities, (int, float)) and assets > 0:
            debt_to_assets = (liabilities / assets) * 100
            
            # Create balance sheet card
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div style="display: flex; justify-content: space-between; align-items: center;">', unsafe_allow_html=True)
            st.markdown(f'<h3 style="margin: 0;">Balance Sheet</h3>', unsafe_allow_html=True)
            
            # Debt-to-assets gauge
            if debt_to_assets < 30:
                gauge_color = COLOR_POSITIVE
                rating = "Very Strong"
            elif debt_to_assets < 50:
                gauge_color = "#2ecc71"  # Lighter green
                rating = "Strong"
            elif debt_to_assets < 70:
                gauge_color = "#f1c40f"  # Yellow
                rating = "Moderate"
            else:
                gauge_color = COLOR_NEGATIVE
                rating = "Leveraged"
            
            st.markdown(f'<span class="badge" style="background-color: {gauge_color}; color: white;">{rating}</span>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Debt-to-assets details
            st.markdown(f'<p>Debt-to-Assets Ratio: <strong>{debt_to_assets:.2f}%</strong></p>', unsafe_allow_html=True)
            
            # Add gauge visualization
            gauge_pct = min(100, max(0, debt_to_assets))  # Scale so 100% debt-to-assets = 100% of gauge
            st.markdown(f'''
            <div style="margin: 10px 0; width: 100%; height: 10px; background-color: rgba(255, 255, 255, 0.1); border-radius: 5px; overflow: hidden;">
                <div style="width: {gauge_pct}%; height: 100%; background-color: {gauge_color};"></div>
            </div>
            ''', unsafe_allow_html=True)
            
            # Add interpretation
            if debt_to_assets < 30:
                st.markdown('<p>With debt at a low percentage of assets, the company has a conservative financial structure.</p>', unsafe_allow_html=True)
            elif debt_to_assets < 50:
                st.markdown('<p>The company maintains a healthy balance sheet with manageable debt levels.</p>', unsafe_allow_html=True)
            elif debt_to_assets < 70:
                st.markdown('<p>The balance sheet is reasonable but has elevated leverage that should be monitored.</p>', unsafe_allow_html=True)
            else:
                st.markdown('<p>The company has high leverage that may pose financial risks, especially in economic downturns.</p>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # If no assessment points available
        if not (isinstance(revenue, (int, float)) and isinstance(net_income, (int, float)) and revenue > 0) and not (isinstance(assets, (int, float)) and isinstance(liabilities, (int, float)) and assets > 0):
            st.markdown('<div class="warning-box">Insufficient data to provide a detailed financial health assessment.</div>', unsafe_allow_html=True)
    
    with tab2:
        # Display SEC filings
        if data.get('sec_edgar_filings') and data['sec_edgar_filings'].get('company_filings'):
            sec_data = data['sec_edgar_filings']['company_filings']
            
            # Try to extract filings from different possible structures
            filings = []
            
            if isinstance(sec_data.get('filings'), dict) and isinstance(sec_data['filings'].get('recent'), list):
                filings = sec_data['filings']['recent']
            elif isinstance(sec_data.get('filings'), list):
                filings = sec_data['filings']
            elif isinstance(sec_data.get('recent'), list):
                filings = sec_data['recent']
            else:
                # Try to find any list containing filing data
                for key, value in sec_data.items():
                    if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                        if 'form' in value[0] or 'filing_date' in value[0] or 'filingDate' in value[0]:
                            filings = value
                            break
            
            if filings:
                st.markdown('<div class="subsection-header">Recent SEC Filings</div>', unsafe_allow_html=True)
                
                # Create a list of filing cards
                for filing in filings[:5]:  # Show up to 5 most recent filings
                    if not isinstance(filing, dict):
                        continue
                        
                    form = filing.get('form', 'N/A')
                    description = filing.get('description', 'N/A')
                    filed_date = filing.get('filingDate', filing.get('filing_date', 'N/A'))
                    
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.markdown(f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">', unsafe_allow_html=True)
                    st.markdown(f'<span class="badge badge-primary">{form}</span>', unsafe_allow_html=True)
                    st.markdown(f'<span style="color: rgba(255, 255, 255, 0.7);">{filed_date}</span>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown(f'<p style="margin: 0;">{description}</p>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="warning-box">No recent SEC filings found.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="warning-box">SEC filing data not available.</div>', unsafe_allow_html=True)

def display_news_summary(data):
    """Display news summary section."""
    st.markdown('<div class="section-header" id="news">Recent News</div>', unsafe_allow_html=True)
    
    if not data.get('news'):
        st.markdown('<div class="warning-box">No recent news available.</div>', unsafe_allow_html=True)
        return
    
    news = data.get('news', [])
    
    # Limit to 5 most recent news items
    recent_news = news[:5] if news else []
    
    if not recent_news:
        st.markdown('<div class="warning-box">No recent news available.</div>', unsafe_allow_html=True)
        return
    
    # Process and display news items
    for article in recent_news:
        if not isinstance(article, dict):
            continue
            
        title = article.get('title', 'No title available')
        
        # Safely get the published date
        published_date = "Unknown date"
        try:
            published_utc = article.get('published_utc')
            if published_utc and isinstance(published_utc, (int, float)):
                published_date = datetime.fromtimestamp(published_utc).strftime('%Y-%m-%d')
            elif published_utc and isinstance(published_utc, str):
                # Try to parse string date
                if published_utc.isdigit():
                    published_date = datetime.fromtimestamp(int(published_utc)).strftime('%Y-%m-%d')
                else:
                    # Try different date formats
                    date_formats = ['%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y', '%d/%m/%Y']
                    for fmt in date_formats:
                        try:
                            published_date = datetime.strptime(published_utc, fmt).strftime('%Y-%m-%d')
                            break
                        except ValueError:
                            continue
        except Exception:
            pass
        
        # Safely get publisher name
        source = "Unknown source"
        publisher = article.get('publisher', {})
        if isinstance(publisher, dict):
            source = publisher.get('name', 'Unknown source')
        
        article_url = article.get('article_url', '#')
        description = article.get('description', 'No description available')
        
        # Create news card
        st.markdown('<div class="news-card">', unsafe_allow_html=True)
        st.markdown(f'<div><span class="news-date">{published_date}</span> &nbsp;|&nbsp; <span class="news-source">{source}</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="news-title">{title}</div>', unsafe_allow_html=True)
        st.markdown(f'<p style="margin-bottom: 10px;">{description}</p>', unsafe_allow_html=True)
        st.markdown(f'<a href="{article_url}" target="_blank" style="color: {COLOR_PRIMARY}; text-decoration: none; font-weight: bold;">Read more <span style="font-size: 1.2em;">→</span></a>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Add news sentiment analysis
    if len(recent_news) > 0:
        st.markdown('<div class="subsection-header">News Sentiment Analysis</div>', unsafe_allow_html=True)
        
        # Basic sentiment analysis based on keywords in titles and descriptions
        positive_keywords = [
            'rise', 'up', 'gain', 'positive', 'profit', 'growth', 'rally', 'surge', 
            'increase', 'beat', 'exceed', 'outperform', 'upgrade', 'strong', 'bullish'
        ]
        
        negative_keywords = [
            'fall', 'down', 'drop', 'negative', 'loss', 'decline', 'sink', 'plunge', 
            'decrease', 'miss', 'underperform', 'downgrade', 'weak', 'bearish'
        ]
        
        positive_count = 0
        negative_count = 0
        total_analyzed = 0
        
        for article in recent_news:
            if not isinstance(article, dict):
                continue
                
            title = article.get('title', '').lower()
            description = article.get('description', '').lower()
            
            # Count keyword matches
            positive_match = False
            negative_match = False
            
            for keyword in positive_keywords:
                if keyword in title or keyword in description:
                    positive_match = True
                    break
            
            for keyword in negative_keywords:
                if keyword in title or keyword in description:
                    negative_match = True
                    break
            
            if positive_match:
                positive_count += 1
            
            if negative_match:
                negative_count += 1
            
            total_analyzed += 1
        
        # Generate sentiment score (-100 to +100)
        if total_analyzed > 0:
            sentiment_score = ((positive_count - negative_count) / total_analyzed) * 100
            
            # Create a gauge chart for sentiment
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = sentiment_score,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "News Sentiment Score", 'font': {'size': 24, 'color': "white"}},
                gauge = {
                    'axis': {'range': [-100, 100], 'tickwidth': 1, 'tickcolor': "white"},
                    'bar': {'color': COLOR_PRIMARY},
                    'bgcolor': "rgba(0, 0, 0, 0.2)",
                    'borderwidth': 2,
                    'bordercolor': "rgba(255, 255, 255, 0.3)",
                    'steps' : [
                        {'range': [-100, -50], 'color': "rgba(231, 76, 60, 0.3)"},
                        {'range': [-50, -20], 'color': "rgba(231, 76, 60, 0.15)"},
                        {'range': [-20, 20], 'color': "rgba(189, 195, 199, 0.15)"},
                        {'range': [20, 50], 'color': "rgba(39, 174, 96, 0.15)"},
                        {'range': [50, 100], 'color': "rgba(39, 174, 96, 0.3)"}
                    ],
                    'threshold': {
                        'line': {'color': COLOR_PRIMARY, 'width': 4},
                        'thickness': 0.75,
                        'value': sentiment_score
                    }
                }
            ))
            
            fig.update_layout(
                height=300, 
                margin=dict(l=20, r=20, t=50, b=20),
                paper_bgcolor="rgba(0, 0, 0, 0.2)",
                font=dict(color="white")
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Add sentiment interpretation
            card_class = ""
            if sentiment_score > 50:
                card_class = "success-box"
                sentiment_text = f"Strongly Positive Sentiment (Score: {sentiment_score:.1f})"
                description = f"The recent news coverage is predominantly positive, which may indicate positive market perception of {data.get('ticker', 'the stock')}."
            elif sentiment_score > 20:
                card_class = "success-box"
                sentiment_text = f"Moderately Positive Sentiment (Score: {sentiment_score:.1f})"
                description = f"The recent news coverage leans positive, suggesting favorable coverage for {data.get('ticker', 'the stock')}."
            elif sentiment_score > -20:
                card_class = "info-box"
                sentiment_text = f"Neutral Sentiment (Score: {sentiment_score:.1f})"
                description = f"The recent news coverage is balanced between positive and negative, indicating mixed perceptions of {data.get('ticker', 'the stock')}."
            elif sentiment_score > -50:
                card_class = "warning-box"
                sentiment_text = f"Moderately Negative Sentiment (Score: {sentiment_score:.1f})"
                description = f"The recent news coverage leans negative, which might suggest some concerns about {data.get('ticker', 'the stock')}."
            else:
                card_class = "error-box"
                sentiment_text = f"Strongly Negative Sentiment (Score: {sentiment_score:.1f})"
                description = f"The recent news coverage is predominantly negative, which could reflect significant challenges facing {data.get('ticker', 'the stock')}."
            
            st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
            st.markdown(f'<h3>{sentiment_text}</h3>', unsafe_allow_html=True)
            st.markdown(f'<p>{description}</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

def display_dividend_information(data):
    """Display dividend information section."""
    st.markdown('<div class="section-header">Dividend Information</div>', unsafe_allow_html=True)
    
    dividends = data.get('dividends', [])
    
    if not dividends:
        st.markdown('<div class="warning-box">No dividend data available.</div>', unsafe_allow_html=True)
        return
    
    # Get the most recent dividend
    latest_dividend = dividends[0] if dividends else None
    
    if not latest_dividend:
        st.markdown('<div class="warning-box">No dividend information available.</div>', unsafe_allow_html=True)
        return
    
    # Extract dividend information
    ex_date = latest_dividend.get('ex_dividend_date', 'N/A')
    pay_date = latest_dividend.get('pay_date', 'N/A')
    
    try:
        dividend_amount = float(latest_dividend.get('cash_amount', 0))
    except (ValueError, TypeError):
        dividend_amount = 0
    
    # Display latest dividend info
    st.markdown('<div class="subsection-header">Latest Dividend</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Dividend Amount</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">${dividend_amount:.4f}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Ex-Dividend Date</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">{ex_date}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Payment Date</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">{pay_date}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Calculate and display annual yield if possible
    if data.get('recent_aggregates') and dividend_amount > 0:
        try:
            latest_price = float(data['recent_aggregates'][-1]['c'])
            
            if latest_price > 0:
                # Calculate annual yield (assuming quarterly dividends)
                annual_yield = (dividend_amount * 4) / latest_price * 100
                
                st.markdown('<div class="subsection-header">Dividend Yield</div>', unsafe_allow_html=True)
                
                # Create a yield card
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.markdown('<div class="metric-label">Annual Dividend Yield</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-value">{annual_yield:.2f}%</div>', unsafe_allow_html=True)
                
                # Add some context about the yield
                if annual_yield > 5:
                    st.markdown('<div style="margin-top: 10px;">High yield compared to market average</div>', unsafe_allow_html=True)
                elif annual_yield > 2:
                    st.markdown('<div style="margin-top: 10px;">Moderate yield compared to market average</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="margin-top: 10px;">Below average yield compared to market average</div>', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
        except (IndexError, KeyError, ValueError, TypeError):
            pass
    
    # Display dividend history if available
    if len(dividends) > 1:
        st.markdown('<div class="subsection-header">Dividend History</div>', unsafe_allow_html=True)
        
        # Prepare data for chart
        div_history = []
        for div in dividends[:10]:  # Show the last 10 dividends
            try:
                div_date = div.get('ex_dividend_date', 'N/A')
                div_amount = float(div.get('cash_amount', 0))
                div_history.append({
                    'date': div_date,
                    'amount': div_amount
                })
            except (ValueError, TypeError):
                continue
        
        if div_history:
            # Create chart
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=[item['date'] for item in div_history],
                y=[item['amount'] for item in div_history],
                marker=dict(color=COLOR_PRIMARY),
                name='Dividend Amount'
            ))
            
            fig.update_layout(
                title="Recent Dividend History",
                title_font=dict(size=20, color="white"),
                xaxis_title="Ex-Dividend Date",
                yaxis_title="Amount ($)",
                height=400,
                margin=dict(l=0, r=0, t=60, b=0),
                plot_bgcolor="rgba(0, 0, 0, 0.2)",
                paper_bgcolor="rgba(0, 0, 0, 0.2)",
                hovermode="x unified",
                yaxis=dict(
                    gridcolor="rgba(255, 255, 255, 0.1)",
                    tickprefix="$",
                    tickfont=dict(color="white")
                ),
                xaxis=dict(
                    gridcolor="rgba(255, 255, 255, 0.1)",
                    tickfont=dict(color="white")
                ),
                font=dict(color="white")
            )
            
            st.plotly_chart(fig, use_container_width=True)

def display_analyst_recommendations(data):
    """Display analyst recommendations section."""
    st.markdown('<div class="section-header">Analyst Recommendations</div>', unsafe_allow_html=True)
    
    if not data.get('recommendations'):
        st.markdown('<div class="warning-box">No analyst recommendations available.</div>', unsafe_allow_html=True)
        return
    
    recommendations = data.get('recommendations', [])
    
    if not recommendations:
        st.markdown('<div class="warning-box">No analyst recommendations available.</div>', unsafe_allow_html=True)
        return
    
    # Count recommendation types
    rec_counts = {
        'buy': 0,
        'overweight': 0,
        'hold': 0,
        'underweight': 0,
        'sell': 0
    }
    
    total_recs = 0
    latest_date = None
    
    for rec in recommendations:
        if not isinstance(rec, dict):
            continue
            
        action = rec.get('action', '').lower()
        date = rec.get('date', '')
        
        # Update latest date
        if not latest_date or date > latest_date:
            latest_date = date
        
        # Map recommendation to one of our categories
        if action in ['buy', 'strong buy']:
            rec_counts['buy'] += 1
        elif action in ['overweight', 'outperform']:
            rec_counts['overweight'] += 1
        elif action in ['hold', 'neutral', 'market perform']:
            rec_counts['hold'] += 1
        elif action in ['underweight', 'underperform']:
            rec_counts['underweight'] += 1
        elif action in ['sell', 'strong sell']:
            rec_counts['sell'] += 1
        
        total_recs += 1
    
    if total_recs == 0:
        st.markdown('<div class="warning-box">No valid analyst recommendations found.</div>', unsafe_allow_html=True)
        return
    
    # Create donut chart
    fig = go.Figure()
    
    labels = ['Buy', 'Overweight', 'Hold', 'Underweight', 'Sell']
    values = [rec_counts['buy'], rec_counts['overweight'], rec_counts['hold'], rec_counts['underweight'], rec_counts['sell']]
    colors = [COLOR_POSITIVE, '#2ecc71', COLOR_NEUTRAL, '#e67e22', COLOR_NEGATIVE]
    
    fig.add_trace(go.Pie(
        labels=labels,
        values=values,
        hole=0.5,
        marker=dict(colors=colors),
        textinfo='percent',
        hoverinfo='label+value+percent',
        textfont=dict(size=14, color="white")
    ))
    
    # Add a center text with total count
    fig.update_layout(
        title=f"Analyst Recommendations (as of {latest_date})",
        title_font=dict(size=20, color="white"),
        annotations=[dict(
            text=f"{total_recs}<br>Analysts",
            x=0.5, y=0.5,
            font=dict(size=20, color="white"),
            showarrow=False
        )],
        height=400,
        margin=dict(l=0, r=0, t=60, b=0),
        paper_bgcolor="rgba(0, 0, 0, 0.2)",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5,
            font=dict(color="white")
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Generate consensus rating
    if total_recs > 0:
        # Calculate consensus score (1-5 scale, where 1 is Strong Buy and 5 is Strong Sell)
        consensus_score = (1*rec_counts['buy'] + 2*rec_counts['overweight'] + 3*rec_counts['hold'] + 
                           4*rec_counts['underweight'] + 5*rec_counts['sell']) / total_recs
        
        # Determine consensus text
        if consensus_score < 1.5:
            consensus_text = "Strong Buy"
            consensus_color = COLOR_POSITIVE
        elif consensus_score < 2.5:
            consensus_text = "Buy"
            consensus_color = "#2ecc71"
        elif consensus_score < 3.5:
            consensus_text = "Hold"
            consensus_color = COLOR_NEUTRAL
        elif consensus_score < 4.5:
            consensus_text = "Sell"
            consensus_color = "#e67e22"
        else:
            consensus_text = "Strong Sell"
            consensus_color = COLOR_NEGATIVE
        
        # Display consensus card
        st.markdown('<div class="card" style="text-align: center;">', unsafe_allow_html=True)
        st.markdown(f'<h3>Analyst Consensus</h3>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-size: 2.5rem; font-weight: bold; color: {consensus_color}; margin: 15px 0;">{consensus_text}</div>', unsafe_allow_html=True)
        
        # Add visual scale
        st.markdown('''
        <div style="display: flex; justify-content: space-between; margin: 20px 0;">
            <div style="text-align: center; width: 20%;">
                <div style="font-weight: bold;">Strong Buy</div>
            </div>
            <div style="text-align: center; width: 20%;">
                <div style="font-weight: bold;">Buy</div>
            </div>
            <div style="text-align: center; width: 20%;">
                <div style="font-weight: bold;">Hold</div>
            </div>
            <div style="text-align: center; width: 20%;">
                <div style="font-weight: bold;">Sell</div>
            </div>
            <div style="text-align: center; width: 20%;">
                <div style="font-weight: bold;">Strong Sell</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        # Add indicator on the scale
        position_pct = ((consensus_score - 1) / 4) * 100
        st.markdown(f'''
        <div style="position: relative; height: 8px; background: linear-gradient(to right, {COLOR_POSITIVE}, #2ecc71, {COLOR_NEUTRAL}, #e67e22, {COLOR_NEGATIVE}); border-radius: 4px; margin-bottom: 30px;">
            <div style="position: absolute; top: -10px; left: {position_pct}%; transform: translateX(-50%); width: 20px; height: 20px; background-color: {consensus_color}; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.2);"></div>
        </div>
        ''', unsafe_allow_html=True)
        
        st.markdown(f'<p>Based on {total_recs} analyst recommendations</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

def display_summary_dashboard(data):
    """Display summary dashboard with key metrics."""
    st.markdown('<div class="section-header">Dashboard Summary</div>', unsafe_allow_html=True)
    
    # Create a card with key metrics
    st.markdown('<div class="summary-box">', unsafe_allow_html=True)
    
    # Create title with stock name and ticker
    ticker = data.get('ticker', 'N/A')
    name = data.get('details', {}).get('name', 'N/A')
    
    st.markdown(f'<h2 style="text-align: center; margin-bottom: 20px;">{name} ({ticker}) - Key Metrics</h2>', unsafe_allow_html=True)
    
    # Create three columns for metrics
    col1, col2, col3 = st.columns(3)
    
    # Column 1: Price metrics
    with col1:
        st.markdown('<h3 style="text-align: center;">Price</h3>', unsafe_allow_html=True)
        
        # Get latest price
        latest_price = None
        if data.get('recent_aggregates'):
            try:
                latest_price = float(data['recent_aggregates'][-1]['c'])
                st.markdown(f'<div style="text-align: center; font-size: 1.8rem; font-weight: bold;">${latest_price:.2f}</div>', unsafe_allow_html=True)
                
                # Get price change
                if len(data['recent_aggregates']) > 1:
                    prev_price = float(data['recent_aggregates'][-2]['c'])
                    price_change = latest_price - prev_price
                    price_change_pct = (price_change / prev_price) * 100
                    
                    if price_change >= 0:
                        st.markdown(f'<div style="text-align: center; color: {COLOR_POSITIVE};">+${price_change:.2f} (+{price_change_pct:.2f}%)</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div style="text-align: center; color: {COLOR_NEGATIVE};">-${abs(price_change):.2f} ({price_change_pct:.2f}%)</div>', unsafe_allow_html=True)
            except (KeyError, ValueError, TypeError, IndexError):
                st.markdown('<div style="text-align: center; font-size: 1.8rem; font-weight: bold;">N/A</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="text-align: center; font-size: 1.8rem; font-weight: bold;">N/A</div>', unsafe_allow_html=True)
    
    # Column 2: Financial metrics
    with col2:
        st.markdown('<h3 style="text-align: center;">Financials</h3>', unsafe_allow_html=True)
        
        # Extract financial metrics if available
        if data.get('financials'):
            latest_report = data['financials'][0] if data['financials'] else None
            
            if latest_report:
                metrics = extract_financial_metrics(latest_report)
                
                if metrics.get('Net Income'):
                    net_income = metrics['Net Income']
                    net_income_value = parse_financial_value(net_income)
                    
                    if net_income_value is not None:
                        if net_income_value >= 0:
                            st.markdown(f'<div style="text-align: center; font-size: 1.2rem; margin-bottom: 5px;"><span style="font-weight: bold;">Net Income:</span> <span style="color: {COLOR_POSITIVE};">{net_income}</span></div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div style="text-align: center; font-size: 1.2rem; margin-bottom: 5px;"><span style="font-weight: bold;">Net Income:</span> <span style="color: {COLOR_NEGATIVE};">{net_income}</span></div>', unsafe_allow_html=True)
                
                if metrics.get('EPS'):
                    eps = metrics['EPS']
                    eps_value = parse_financial_value(eps)
                    
                    if eps_value is not None:
                        if eps_value >= 0:
                            st.markdown(f'<div style="text-align: center; font-size: 1.2rem;"><span style="font-weight: bold;">EPS:</span> <span style="color: {COLOR_POSITIVE};">{eps}</span></div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div style="text-align: center; font-size: 1.2rem;"><span style="font-weight: bold;">EPS:</span> <span style="color: {COLOR_NEGATIVE};">{eps}</span></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div style="text-align: center; font-size: 1.2rem;">No financial data available</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="text-align: center; font-size: 1.2rem;">No financial data available</div>', unsafe_allow_html=True)
    
    # Column 3: Technical indicators
    with col3:
        st.markdown('<h3 style="text-align: center;">Technical</h3>', unsafe_allow_html=True)
        
        # Calculate RSI if we have enough data
        rsi_value = None
        if data.get('recent_aggregates') and len(data['recent_aggregates']) >= 14:
            prices = []
            for bar in data['recent_aggregates']:
                try:
                    prices.append(float(bar['c']))
                except (KeyError, ValueError, TypeError):
                    continue
            
            if len(prices) >= 14:
                rsi_value = calculate_rsi(prices, 14)[-1] if calculate_rsi(prices, 14) else None
        
        if rsi_value is not None:
            # RSI signal
            if rsi_value < 30:
                st.markdown(f'<div style="text-align: center; font-size: 1.2rem; margin-bottom: 5px;"><span style="font-weight: bold;">RSI:</span> <span style="color: {COLOR_POSITIVE};">{rsi_value:.2f} (Oversold)</span></div>', unsafe_allow_html=True)
            elif rsi_value > 70:
                st.markdown(f'<div style="text-align: center; font-size: 1.2rem; margin-bottom: 5px;"><span style="font-weight: bold;">RSI:</span> <span style="color: {COLOR_NEGATIVE};">{rsi_value:.2f} (Overbought)</span></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div style="text-align: center; font-size: 1.2rem; margin-bottom: 5px;"><span style="font-weight: bold;">RSI:</span> {rsi_value:.2f} (Neutral)</span></div>', unsafe_allow_html=True)
        
        # Get SMA value
        sma_value = None
        if data.get('sma_50') and data['sma_50'].get('values'):
            try:
                sma_value = float(data['sma_50']['values'][-1]['value'])
            except (IndexError, KeyError, ValueError, TypeError):
                pass
        
        if latest_price is not None and sma_value is not None:
            if latest_price > sma_value:
                st.markdown(f'<div style="text-align: center; font-size: 1.2rem;"><span style="font-weight: bold;">SMA:</span> <span style="color: {COLOR_POSITIVE};">Price > SMA (Bullish)</span></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div style="text-align: center; font-size: 1.2rem;"><span style="font-weight: bold;">SMA:</span> <span style="color: {COLOR_NEGATIVE};">Price < SMA (Bearish)</span></div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def main():
    """Main function to run the dashboard."""
    st.markdown('<h1 class="main-header">Stock Analysis Dashboard</h1>', unsafe_allow_html=True)
    
    # Add dashboard description with improved styling
    st.markdown("""
    <div class="info-box animate-fade-in">
        <p>This interactive dashboard provides comprehensive analysis of stock performance, financial health, and market sentiment.</p>
        <p>Enter a stock ticker below to analyze the stock.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for user input with improved styling
    st.sidebar.markdown('<div class="logo-text">StockInsights</div>', unsafe_allow_html=True)
    st.sidebar.markdown('<hr>', unsafe_allow_html=True)
    
    # Add ticker input
    ticker = st.sidebar.text_input("Enter Stock Ticker:", value="AAPL").upper()
    
    # Add analysis button with better styling
    analyze_button = st.sidebar.button("Analyze Stock", type="primary")
    
    # Initialize session state
    if 'analyzed_ticker' not in st.session_state:
        st.session_state.analyzed_ticker = None
    
    # Check if we should analyze the stock
    run_analysis = False
    
    if analyze_button:
        if ticker:
            run_analysis = True
            st.session_state.analyzed_ticker = ticker
    elif st.session_state.analyzed_ticker:
        # Allow re-running the analysis on page refresh
        ticker = st.session_state.analyzed_ticker
        run_analysis = True
    
    # Run the analysis if triggered
    if run_analysis and ticker:
        # Display the sticky navigation
        display_sticky_nav()
        
        # Show a better loading spinner
        with st.spinner(f"Analyzing {ticker}..."):
            # Get stock data
            data = get_stock_data(ticker)
        
        if data:
            # Display summary dashboard
            display_summary_dashboard(data)
            
            # Display company overview
            display_company_overview(data)
            
            # Display price chart
            display_price_chart(data)
            
            # Display technical analysis
            display_technical_analysis(data)
            
            # Display financial highlights
            display_financial_highlights(data)
            
            # Display analyst recommendations
            display_analyst_recommendations(data)
            
            # Display dividend information
            display_dividend_information(data)
            
            # Display news summary
            display_news_summary(data)
            
            # Add disclaimer
            st.markdown("""
            <div class="disclaimer">
                <p>Disclaimer: This dashboard is for informational purposes only and should not be considered financial advice. 
                Always conduct your own research before making investment decisions.</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        # Display enhanced welcome message if no ticker is analyzed yet
        st.markdown("""
        <div class="welcome-card animate-fade-in">
            <h2 class="welcome-title">Welcome to the Stock Analysis Dashboard</h2>
            <p class="welcome-subtitle">Enter a stock ticker in the sidebar and click "Analyze Stock" to get started.</p>
            <div class="welcome-icons">
                <span class="welcome-icon">📊</span>
                <span class="welcome-icon">📈</span>
                <span class="welcome-icon">💹</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()