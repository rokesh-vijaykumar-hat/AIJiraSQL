# AI SQL Agent - API Reference

This document provides detailed information about all available API endpoints, request formats, response formats, and error handling.

## Base URL

All API endpoints are relative to the base URL of the API Gateway:

```
http://localhost:5000
```

## Authentication

Currently, the API does not implement authentication mechanisms. Authentication can be added as part of future extensions.

## Response Format

All API responses follow a consistent format:

### Success Response

```json
{
  "success": true,
  "data": { ... },  // Response data specific to each endpoint
  "message": "Operation completed successfully"  // Human-readable message
}
```

### Error Response

```json
{
  "success": false,
  "message": "Error message describing what went wrong"
}
```

## API Endpoints

### Health Check API

#### Get System Health

```
GET /api/health
```

Check the health status of all system components.

**Response:**

```json
{
  "status": "ok",  // or "degraded" if some services are unhealthy
  "services": {
    "gateway": "healthy",
    "database": "connected",  // or "not configured", "error: ..."
    "jira": "configured",  // or "not configured"
    "ai_integration": "healthy",  // or "not configured", "error: ..."
    "ai_integration_mode": "agent"  // or "direct"
  }
}
```

### SQL API

#### Generate SQL

```
POST /api/sql/generate
```

Generate SQL from a natural language query without executing it.

**Request Body:**

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| query | string | Natural language query to convert to SQL | Yes |
| jira_issue_key | string | Jira issue key for additional context | No |
| additional_context | string | Any additional context information | No |

**Response:**

```json
{
  "success": true,
  "data": {
    "sql": "SELECT * FROM customers WHERE total_purchases > 1000",
    "explanation": "This query fetches all customers whose total purchases exceed $1000.",
    "mode": "agent"  // or "direct"
  },
  "message": "Query generated successfully"
}
```

#### Execute SQL

```
POST /api/sql/execute
```

Generate SQL from a natural language query, execute it against the database, and explain the results.

**Request Body:**

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| query | string | Natural language query to convert to SQL | Yes |
| jira_issue_key | string | Jira issue key for additional context | No |
| additional_context | string | Any additional context information | No |

**Response:**

```json
{
  "success": true,
  "data": {
    "sql": "SELECT * FROM customers WHERE total_purchases > 1000",
    "results": [
      {
        "id": 1,
        "name": "John Doe",
        "total_purchases": 1500.50
      },
      // More results...
    ],
    "row_count": 1,
    "execution_time_ms": 42.5,
    "explanation": "The query found 1 customer (John Doe) who has made purchases over $1000, specifically $1,500.50.",
    "mode": "agent"  // or "direct"
  },
  "message": "Query executed successfully"
}
```

### Database API

#### Get Database Schema

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

### Jira API

#### Get Jira Issue

```
GET /api/jira/issues/{issue_key}
```

Retrieve details for a specific Jira issue.

**URL Parameters:**

| Parameter | Description |
|-----------|-------------|
| issue_key | The Jira issue key (e.g., PROJECT-123) |

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

Extract context from a Jira issue for use in natural language to SQL conversion.

**URL Parameters:**

| Parameter | Description |
|-----------|-------------|
| issue_key | The Jira issue key (e.g., PROJECT-123) |

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

## Error Codes

The API uses standard HTTP status codes to indicate the success or failure of an API request:

| Status Code | Description |
|-------------|-------------|
| 200 | OK - The request was successful |
| 400 | Bad Request - The request was invalid or malformed |
| 404 | Not Found - The requested resource was not found |
| 500 | Internal Server Error - An error occurred on the server |
| 503 | Service Unavailable - Required services (OpenAI, AI Agent, etc.) are not available |

## Rate Limiting

Currently, the API does not implement rate limiting. This can be added as part of future extensions.

## Examples

### Example 1: Generate SQL

**Request:**

```bash
curl -X POST http://localhost:5000/api/sql/generate \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me all customers who made purchases over $1000 in the last month",
    "additional_context": "Focus on US customers only"
  }'
```

**Response:**

```json
{
  "success": true,
  "data": {
    "sql": "SELECT c.* FROM customers c JOIN orders o ON c.id = o.customer_id WHERE o.amount > 1000 AND o.order_date >= CURRENT_DATE - INTERVAL '1 month' AND c.country = 'USA'",
    "explanation": "This query retrieves all customers from the USA who have placed orders worth more than $1000 in the past month. It joins the customers table with the orders table based on the customer ID.",
    "mode": "agent"
  },
  "message": "Query generated successfully using AI Agent"
}
```

### Example 2: Execute SQL with Jira Context

**Request:**

```bash
curl -X POST http://localhost:5000/api/sql/execute \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Identify our top spending customers",
    "jira_issue_key": "SALES-123"
  }'
```

**Response:**

```json
{
  "success": true,
  "data": {
    "sql": "SELECT c.id, c.name, c.email, SUM(o.amount) as total_spent FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.id, c.name, c.email ORDER BY total_spent DESC LIMIT 10",
    "results": [
      {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "total_spent": 1245.50
      },
      {
        "id": 3,
        "name": "Robert Brown",
        "email": "robert@example.com",
        "total_spent": 785.25
      }
    ],
    "row_count": 2,
    "execution_time_ms": 58.3,
    "explanation": "The query identifies the top spending customers by calculating the total amount spent by each customer across all their orders. John Doe is the highest spender with $1,245.50 in total purchases, followed by Robert Brown with $785.25.",
    "mode": "direct"
  },
  "message": "Query executed successfully"
}
```