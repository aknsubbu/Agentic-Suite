# TalkToCSV: Conversational CSV Analysis Tool

TalkToCSV is an interactive application that lets you chat with your CSV data in plain English. Upload a CSV file and ask questions about your data to get instant insights, visualizations, and analysis without writing code.

## Features

- 💬 **Natural Language Interface**: Ask questions about your data in plain English
- 📊 **Automatic Visualizations**: Get appropriate charts and graphs based on your queries
- 📈 **Comprehensive Analysis**: Automatic data profiling and statistical analysis
- 🔄 **Conversation Memory**: Follow-up questions with context from previous interactions
- 📁 **Support for Large Files**: Chunk-based uploading for large CSV files
- 🛡️ **Secure Code Execution**: Safe execution of generated code

## Architecture

The application consists of two main components:

- **Frontend**: A Streamlit web application that provides the user interface
- **Backend**: A FastAPI service that processes CSV files, generates and executes code, and communicates with the LLM

## Installation

### Prerequisites

- Python 3.8+
- OpenAI API key

### Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/TalkToCSV.git
   cd TalkToCSV
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Running the Application

### Start the Backend

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Start the Frontend

```bash
cd frontend
streamlit run app.py
```

Then open your browser and navigate to http://localhost:8501

## Using TalkToCSV

1. **Upload a CSV file** using the file uploader in the sidebar
2. **Explore your data** in the Data Explorer tab
3. **View automatic analysis** in the Analysis Dashboard tab
4. **Ask questions** about your data in the Chat tab

### Example Queries

- "What is this data about?"
- "Show me the first 10 rows"
- "What is the average value in the Amount column?"
- "How many transactions were made per category?"
- "Show me a bar chart of sales by region"
- "What was the total revenue in 2023?"
- "Which product category has the highest average sales?"

## Project Structure

```
TalkToCSV/
├── frontend/
│   └── app.py           # Streamlit frontend application
├── backend/
│   ├── __init__.py
│   ├── main.py          # FastAPI application
│   ├── csv_processor.py # CSV file handling and analysis
│   ├── code_executor.py # Safe code execution
│   ├── llm_agent.py     # LLM integration
│   └── simpler_code_generation.py # Predefined code templates
├── requirements.txt     # Project dependencies
└── .env                 # Environment variables (not in repo)
```

## How It Works

1. **CSV Upload**: Files are uploaded, processed, and analyzed for basic statistics
2. **Query Processing**: Natural language queries are transformed into Python code
3. **Code Execution**: Generated code is executed in a sandboxed environment
4. **Response Generation**: Results are converted to natural language and visualizations

## Dependencies

The main dependencies include:

- streamlit: For the web interface
- fastapi: For the backend API
- pandas: For data processing
- langchain: For LLM interactions
- openai: For the GPT-4 integration
- plotly: For interactive visualizations
