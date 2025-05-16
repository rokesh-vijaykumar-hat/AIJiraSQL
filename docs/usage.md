# AI SQL Agent - Usage Guide

## Overview

The AI SQL Agent provides a robust interface for translating natural language queries into SQL, executing those queries, and explaining the results. The system supports two modes of AI integration:

1. **Direct Mode**: Uses OpenAI's API directly for natural language to SQL conversion and results explanation.
2. **Agent Mode**: Uses a separate AI Agent service, which is run as an isolated container.

This flexibility allows you to choose the most appropriate approach based on your requirements, security considerations, or performance needs.

## Configuration

The system is configured via environment variables:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `AI_INTERACTION_MODE` | The AI interaction mode to use (`direct` or `agent`) | `agent` | No |
| `OPENAI_API_KEY` | OpenAI API key (required for `direct` mode) | - | Yes (for `direct` mode) |
| `AI_AGENT_URL` | URL of the AI Agent service (required for `agent` mode) | `http://localhost:8080` | Yes (for `agent` mode) |
| `DATABASE_URL` | PostgreSQL connection string | - | Yes |
| `PGHOST` | PostgreSQL host | - | Yes |
| `PGDATABASE` | PostgreSQL database name | - | Yes |
| `PGUSER` | PostgreSQL username | - | Yes |
| `PGPASSWORD` | PostgreSQL password | - | Yes |
| `PGPORT` | PostgreSQL port | `5432` | No |
| `JIRA_URL` | Jira API URL | - | No |
| `JIRA_USER_EMAIL` | Jira user email | - | No |
| `JIRA_API_TOKEN` | Jira API token | - | No |

## API Endpoints

### Health Check

```
GET /api/health
```

Check the health status of all services.

**Response:**
```json
{
  "status": "ok",
  "services": {
    "gateway": "healthy",
    "database": "connected",
    "jira": "configured",
    "ai_integration": "healthy",
    "ai_integration_mode": "agent"
  }
}
```

### Generate SQL

```
POST /api/sql/generate
```

Generate SQL from a natural language query without executing it.

**Request Body:**
```json
{
  "query": "Show me all customers who made purchases over $1000 in the last month",
  "jira_issue_key": "SALES-123",  // Optional
  "additional_context": "Focus on US customers only"  // Optional
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "sql": "SELECT c.* FROM customers c JOIN orders o ON c.id = o.customer_id WHERE o.amount > 1000 AND o.order_date >= CURRENT_DATE - INTERVAL '1 month' AND c.country = 'USA'",
    "explanation": "This query retrieves all customers who have placed orders worth more than $1000 in the past month, specifically filtering for customers based in the USA.",
    "mode": "agent"
  },
  "message": "Query generated successfully using AI Agent"
}
```

### Execute SQL Query

```
POST /api/sql/execute
```

Generate and execute a SQL query from a natural language query, then explain the results.

**Request Body:**
```json
{
  "query": "Show me all customers who made purchases over $1000 in the last month",
  "jira_issue_key": "SALES-123",  // Optional
  "additional_context": "Focus on US customers only"  // Optional
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "sql": "SELECT c.* FROM customers c JOIN orders o ON c.id = o.customer_id WHERE o.amount > 1000 AND o.order_date >= CURRENT_DATE - INTERVAL '1 month' AND c.country = 'USA'",
    "results": [
      {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "country": "USA",
        "created_at": "2023-01-15"
      }
    ],
    "row_count": 1,
    "execution_time_ms": 42.5,
    "explanation": "The query found 1 customer (John Doe) who made a purchase over $1000 in the last month. This customer is based in the USA and placed the order on 2023-04-05 for a total of $1,245.50.",
    "mode": "agent"
  },
  "message": "Query executed successfully"
}
```

### Get Database Schema

```
GET /api/db/schema
```

Retrieve the database schema information.

**Response:**
```json
{
  "success": true,
  "data": {
    "tables": [
      {
        "name": "customers",
        "columns": [
          {
            "name": "id",
            "type": "integer",
            "is_nullable": false,
            "is_primary_key": true,
            "is_foreign_key": false
          },
          // More columns...
        ]
      },
      // More tables...
    ],
    "relationships": [
      {
        "from": "orders.customer_id",
        "to": "customers.id"
      },
      // More relationships...
    ]
  },
  "message": "Schema retrieved successfully"
}
```

### Jira Integration

The system can retrieve context from Jira issues to enhance SQL generation.

#### Get Jira Issue

```
GET /api/jira/issues/{issue_key}
```

Retrieve a Jira issue by its key.

**Response:**
```json
{
  "success": true,
  "data": {
    "key": "SALES-123",
    "summary": "Analyze high-value customers",
    "description": "We need a report of all customers who have made purchases over $1000 in the last 3 months.",
    "status": "Open",
    "issue_type": "Task",
    "created": "2023-04-01T10:00:00.000Z",
    "updated": "2023-04-02T14:30:00.000Z",
    "priority": "High"
  },
  "message": "Issue retrieved successfully"
}
```

#### Extract Context from Jira Issue

```
GET /api/jira/context/{issue_key}
```

Extract context from a Jira issue for use in SQL generation.

**Response:**
```json
{
  "success": true,
  "data": {
    "issue_key": "SALES-123",
    "context": "Jira Issue: SALES-123 - Analyze high-value customers\nStatus: Open\nType: Task\nPriority: High\n\nDescription:\nWe need a report of all customers who have made purchases over $1000 in the last 3 months."
  },
  "message": "Context extracted successfully"
}
```

## Examples

### Using Direct Mode

To use Direct Mode, set the environment variable:

```
AI_INTERACTION_MODE=direct
OPENAI_API_KEY=your_openai_api_key
```

This will use OpenAI's API directly for SQL generation and result explanation.

### Using Agent Mode

To use Agent Mode, set the environment variable:

```
AI_INTERACTION_MODE=agent
AI_AGENT_URL=http://ai-agent:8080  # Adjust to your AI Agent service URL
```

This will forward requests to the separate AI Agent service for SQL generation and result explanation.

## Error Handling

The API returns appropriate HTTP status codes and error messages:

- `400 Bad Request`: Missing or invalid parameters
- `500 Internal Server Error`: Server-side errors
- `503 Service Unavailable`: Required services (OpenAI, AI Agent, etc.) are not available

All error responses follow this format:

```json
{
  "success": false,
  "message": "Detailed error message"
}
```