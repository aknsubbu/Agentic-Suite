# AI-Powered Agentic Suite

A collection of sophisticated proof-of-concept (POC) projects showcasing advanced data analysis, AI integration, and natural language processing capabilities. These projects are designed for sales demonstrations and client presentations.

## Project Portfolio

### 1. Financial Research Company - US Stock Exchange

Advanced stock analysis dashboard providing comprehensive market insights.

**Key Features:**

- Interactive price charts with technical indicators
- Financial metrics analysis and visualization
- News sentiment analysis with AI scoring
- Automated PDF report generation
- Real-time market data integration
- Balance sheet and financial health assessment
- Dividend analysis and tracking

**Tech Stack:** Python, Streamlit, Plotly, ReportLab, Pandas

### 2. Talk To CSV

Natural language interface for CSV data analysis.

**Key Features:**

- Conversational AI for data exploration
- Automatic visualization suggestions
- Statistical analysis automation
- Context-aware query processing
- Large file support with chunking
- Secure code execution environment

**Tech Stack:** Python, FastAPI, Streamlit, LangChain, OpenAI

### 3. Talk To DB (In Development)

Conversational database query interface.

**Key Features:**

- Natural language to SQL translation
- Interactive query building
- Multi-database support
- Role-based access control
- Query history tracking
- Result visualization

**Tech Stack:** Python, Streamlit, MongoDB, SQL, LLM integration

## Version Information

- Financial Research Dashboard: v1.2.0
- Talk To CSV: v0.9.1
- Talk To DB: v0.5.0 (Beta)

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 14+ (for web interfaces)
- Git
- Virtual environment tool (venv/conda)

### Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/POC_Sale_Projects.git
cd POC_Sale_Projects
```

2. Set up individual projects:

**Financial Research Dashboard:**

```bash
cd Financial_Research_Company_USStockExchange
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Talk To CSV:**

```bash
cd TalkToCSV
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Talk To DB:**

```bash
cd TalkToDB
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Configuration

1. Copy sample environment files:

```bash
cp Financial_Research_Company_USStockExchange/.env.sample Financial_Research_Company_USStockExchange/.env
cp TalkToCSV/.env.sample TalkToCSV/.env
cp TalkToDB/.env.sample TalkToDB/.env
```

2. Update environment variables with your API keys and configurations

## Usage

### Financial Research Dashboard

```bash
cd Financial_Research_Company_USStockExchange
streamlit run app.py
```

Access at: http://localhost:8501

### Talk To CSV

```bash
# Terminal 1 - Backend
cd TalkToCSV/backend
uvicorn main:app --reload

# Terminal 2 - Frontend
cd TalkToCSV/frontend
streamlit run app.py
```

Access at: http://localhost:8501

### Talk To DB

```bash
cd TalkToDB/frontend
streamlit run app.py
```

Access at: http://localhost:8501

## Project Structure

```
POC_Sale_Projects/
├── Financial_Research_Company_USStockExchange/
│   ├── app.py
│   ├── InfoFetch.py
│   ├── ReportGeneration.py
│   └── reports/
├── TalkToCSV/
│   ├── frontend/
│   │   └── app.py
│   └── backend/
│       └── main.py
├── TalkToDB/
│   ├── frontend/
│   │   └── app.py
│   └── backend/
│       └── main.py
└── README.md
```

## Development

### Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

### Coding Standards

- Follow PEP 8 for Python code
- Write comprehensive docstrings
- Maintain test coverage
- Update documentation

## License

Copyright © 2024 Your Company Name
All rights reserved.

These projects contain proprietary and confidential information. Distribution, reproduction, or use without explicit written permission is strictly prohibited.

## Disclaimer

These projects are demonstrations and proofs of concept. They are not intended for production use without proper review and modification. No warranty is provided, and use is at your own risk.
