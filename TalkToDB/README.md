# TalkToDB: Natural Language Interface for MongoDB

TalkToDB is a powerful tool that enables users to interact with MongoDB databases using natural language. By leveraging AI agents, the application translates plain English queries into MongoDB operations, making database exploration and analysis accessible to users without specialized MongoDB query language knowledge.

## Features

- **Natural Language Queries**: Ask questions about your data in plain English
- **Rich Response Types**: View results as text, tables, or visualizations
- **MongoDB-Specific Tools**: Explore collections, schemas, and sample documents
- **Interactive Experience**: Maintain conversation context with MongoDB agents
- **Exportable Results**: Save and share query results and conversations

## Architecture

TalkToDB uses an agent-based architecture with specialized components:

- **MongoDB Agent System**: Core system that processes natural language queries
- **Response Capture System**: Captures, formats, and displays MongoDB responses
- **Streamlit UI**: Interactive web interface for database interactions

## Installation

### Prerequisites

- Python 3.8+
- MongoDB instance (local or Atlas)
- API keys for LLM services (if using OpenAI, Azure, etc.)

### Setup

1. Clone the repository:

```bash
git clone https://github.com/yourusername/TalkToDB.git
cd TalkToDB
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure your MongoDB connection:

```bash
cp config.example.py config.py
# Edit config.py with your MongoDB connection details
```

4. Run the application:

```bash
streamlit run app.py
```

## Usage Examples

### Basic Queries

```
"Show me all customers who spent more than $1000 last month"
"What products have the highest ratings?"
"Count documents in the users collection by country"
```

### Visualizations

```
"Create a bar chart showing sales by region"
"Visualize the distribution of customer ages"
"Plot order volumes over the last 6 months"
```

### Schema Exploration

```
"Tell me about the users collection"
"What fields are available in the orders collection?"
"Show me a sample document from products"
```

## Response Capture System

The MongoDB Response Capture System is a core component that:

1. Captures and processes various types of responses from MongoDB agents
2. Handles different output formats (text, tables, visualizations)
3. Maintains conversation history
4. Formats MongoDB-specific data for optimal display
5. Provides export capabilities for sharing results

### Key Classes

- **ResponseListener**: Interface for objects that listen to MongoDB agent responses
- **ResponseCapture**: Main class that captures and manages responses
- **MongoDBResponseFormatter**: Formats MongoDB documents and query results

### Extending the System

You can extend TalkToDB by:

1. Creating custom MongoDB agents for specialized tasks
2. Adding new response formatters for domain-specific data
3. Integrating with additional visualization libraries

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
