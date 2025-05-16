# AI SQL Agent

An intelligent SQL agent that converts natural language queries into SQL, executes them against a database, and explains the results. This system supports two different modes of AI integration: direct OpenAI integration or a separate AI agent service.

## Features

- **Natural Language to SQL Conversion**: Convert business questions into SQL queries
- **Query Execution**: Execute the generated SQL queries against your database
- **Result Explanation**: Get clear explanations of query results in plain language
- **Jira Integration**: Use Jira issues as context to generate more accurate SQL
- **Dual AI Integration**: Choose between direct OpenAI API integration or a separate AI agent service

## Architecture

The system is designed with a modular architecture:

- **API Gateway**: Flask-based API for client interactions
- **AI Agent Service**: Separate container for AI operations
- **Database Layer**: PostgreSQL database connection and execution
- **Jira Integration**: Context extraction from Jira issues

For a detailed architectural overview, see [Architecture Documentation](docs/architecture.md).

## Requirements

- Docker and Docker Compose
- PostgreSQL database
- OpenAI API key (if using direct mode)
- Jira API credentials (optional)

## Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ai-sql-agent
```

### 2. Configure Environment Variables

Create a `.env` file in the root directory:

```
# Database Configuration
DATABASE_URL=postgresql://user:password@host:port/dbname
PGHOST=host
PGDATABASE=dbname
PGUSER=user
PGPASSWORD=password
PGPORT=5432

# AI Configuration
AI_INTERACTION_MODE=agent  # Use 'direct' or 'agent'
OPENAI_API_KEY=your_openai_api_key  # Required for 'direct' mode

# AI Agent Service URL (for 'agent' mode)
AI_AGENT_URL=http://ai-agent:8080

# Jira Configuration (Optional)
JIRA_URL=https://your-domain.atlassian.net
JIRA_USER_EMAIL=your-email@example.com
JIRA_API_TOKEN=your_jira_api_token
```

### 3. Build and Start the Services

```bash
docker-compose up -d
```

This will start the API Gateway, AI Agent Service, and PostgreSQL database.

### 4. Verify the Installation

```bash
curl http://localhost:5000/api/health
```

You should see a response with the health status of all services.

## Usage

See the [Usage Documentation](docs/usage.md) for detailed API usage instructions.

### Basic Examples

#### Generate SQL from Natural Language

```bash
curl -X POST http://localhost:5000/api/sql/generate -H "Content-Type: application/json" -d '{
  "query": "Show me all customers who made purchases over $1000 in the last month"
}'
```

#### Execute a Query and Get Results with Explanation

```bash
curl -X POST http://localhost:5000/api/sql/execute -H "Content-Type: application/json" -d '{
  "query": "Show me all customers who made purchases over $1000 in the last month"
}'
```

## Configuration Options

### AI Integration Modes

The system supports two AI integration modes:

1. **Direct Mode**: Uses OpenAI's API directly through the main application.
   - Set `AI_INTERACTION_MODE=direct`
   - Requires `OPENAI_API_KEY`

2. **Agent Mode**: Uses a separate AI Agent service that runs in its own container.
   - Set `AI_INTERACTION_MODE=agent`
   - Set `AI_AGENT_URL` to the URL of the AI Agent service

### Database Configuration

Configure your database connection with standard PostgreSQL environment variables:
- `DATABASE_URL`: Full connection string
- `PGHOST`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`, `PGPORT`: Individual connection parameters

### Jira Integration (Optional)

Configure Jira integration to enhance queries with business context:
- `JIRA_URL`: Your Jira instance URL
- `JIRA_USER_EMAIL`: Your Jira user email
- `JIRA_API_TOKEN`: Your Jira API token

## Documentation

- [Architecture Documentation](docs/architecture.md): Detailed system architecture
- [API Documentation](docs/api.md): Comprehensive API reference
- [Usage Guide](docs/usage.md): Examples and usage instructions
- [Extensibility Guide](docs/extensibility.md): How to extend the system

## License

[MIT License](LICENSE)