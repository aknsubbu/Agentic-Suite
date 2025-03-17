# Proof of Concept Sales Projects

This repository contains several proof-of-concept (POC) projects designed to demonstrate various data analysis and AI capabilities for sales presentations and client demonstrations.

## Projects Overview

### Financial Research Company - US Stock Exchange

A comprehensive stock analysis dashboard and reporting tool that provides detailed financial insights, technical analysis, and automated report generation for US-listed companies.

**Key Features:**

- Interactive stock data visualization with price charts and technical indicators
- Financial highlights extraction and analysis
- News sentiment analysis
- Automated PDF report generation
- Company overview and metrics dashboard

**Technologies:** Python, Streamlit, Pandas, Plotly, ReportLab

### Talk To CSV

A conversational AI agent that allows users to interact with CSV data using natural language queries.

**Key Features:**

- Natural language processing for CSV analysis
- Automatic data profiling and visualization recommendations
- Interactive chat interface for data exploration
- Support for uploading and analyzing large CSV files
- Data visualization based on conversation context

**Technologies:** Python, FastAPI, Streamlit, Pandas, Plotly, LLM integration

### Talk To DB -- (In Progress)

A conversational interface for database interactions, allowing users to query databases using natural language.

**Key Features:**

- Natural language to SQL translation
- Interactive data exploration
- Data visualization capabilities
- Conversation history tracking
- Multi-agent system with specialized roles

**Technologies:** Python, Streamlit, SQL, LLM integration

## Installation

Each project has its own dependencies and setup requirements. Please refer to the individual project directories for specific installation instructions.

### General Requirements

- Python 3.8+
- pip or conda package manager

### Example Setup

```bash
# Clone the repository
git clone [repository-url]

# Navigate to the desired project
cd POC_Sale_Projects/TalkToCSV

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application (example for TalkToCSV)
cd frontend
streamlit run app.py
```

## Usage

### Financial Research Company - US Stock Exchange

```bash
cd Financial_Research_Company_USStockExchange
streamlit run app.py
```

Enter a stock ticker in the sidebar and click "Analyze Stock" to generate a comprehensive analysis.

### Talk To CSV

```bash
# Start the backend server
cd TalkToCSV/backend
uvicorn main:app --reload

# In a new terminal, start the frontend
cd TalkToCSV/frontend
streamlit run app.py
```

Upload a CSV file and start chatting with your data using natural language.

### Talk To DB

```bash
cd TalkToDB/frontend
streamlit run app.py
```

Connect to your database using the connection tab, then start querying your data using natural language.

## Project Structure

Each project follows a similar structure:

- `frontend/` - User interface components
- `backend/` - API and data processing logic
- `logs/` - Application logs
- `cache/` - Cached data
- `reports/` - Generated reports (Financial Research project)

## Contact

For any questions or inquiries about these demonstration projects, please contact [your contact information].
