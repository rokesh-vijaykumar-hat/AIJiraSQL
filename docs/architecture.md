# AI SQL Agent - Architecture

## System Architecture

The AI SQL Agent system is designed with a modular architecture to ensure separation of concerns, scalability, and maintainability. The system consists of the following key components:

### 1. API Gateway (Main Application)

The API Gateway serves as the entry point for all client requests and orchestrates the communication between different components. It is built using Flask and provides the following functionality:

- RESTful API endpoints for generating SQL, executing queries, and retrieving database schema
- Request validation and error handling
- Response formatting and standardization
- Integration with Jira for context extraction
- Database connection management
- AI integration orchestration (choosing between direct OpenAI integration or AI Agent service)

### 2. AI Agent Service

The AI Agent service runs as a separate container and is responsible for the AI-related functionalities:

- Converting natural language to SQL using OpenAI's API
- Explaining SQL query results in natural language
- Providing a RESTful API for the main application to interact with

This separation ensures that:

- The AI capabilities can be scaled independently
- The AI service can be updated or swapped out without affecting the main application
- Security policies can be applied specifically to the AI service
- The architecture supports potential future use of different AI models or services

### 3. Database Layer

The Database Layer provides access to the PostgreSQL database and includes:

- Connection management
- Query execution
- Schema introspection
- Basic security measures for SQL validation

### 4. Jira Integration

The Jira Integration component allows the system to extract relevant business context from Jira issues, enhancing the natural language to SQL conversion process.

## Component Interaction

The following diagram illustrates how the components interact with each other:

```
                                      +-------------------+
                                      |                   |
                                      |  OpenAI API       |
                                      |                   |
                                      +--------^----------+
                                               |
                                               | (Direct Mode)
                                               |
+------------------+                  +--------v----------+
|                  |                  |                   |
|  Client          |  <==>           |  API Gateway      |
|                  |                  |  (Flask)          |
+------------------+                  +--------^----------+
                                               |
                                               | (Agent Mode)
                                               |
                                      +--------v----------+
                                      |                   |
                                      |  AI Agent Service |
                                      |  (FastAPI)        |
                                      +--------^----------+
                                               |
                                               |
                                      +--------v----------+
                                      |                   |
                                      |  Database         |
                                      |  (PostgreSQL)     |
                                      +-------------------+
```

## Data Flow

### SQL Generation Flow

1. Client sends a natural language query to the API Gateway
2. API Gateway retrieves database schema information
3. If Jira issue key is provided, API Gateway extracts context from the Jira issue
4. Based on the configured mode:
   - **Direct Mode**: API Gateway sends the query, schema, and context directly to OpenAI API
   - **Agent Mode**: API Gateway forwards the request to the AI Agent Service, which then interacts with OpenAI API
5. The SQL query is generated and returned to the client

### SQL Execution Flow

1. Client sends a natural language query to the API Gateway
2. API Gateway follows the SQL Generation Flow to obtain a SQL query
3. API Gateway executes the generated SQL query against the database
4. Based on the configured mode:
   - **Direct Mode**: API Gateway sends the results and query to OpenAI API for explanation
   - **Agent Mode**: API Gateway sends the results and query to AI Agent Service for explanation
5. The results and explanation are returned to the client

## Security Considerations

- The API Gateway validates all incoming requests
- SQL queries are validated to prevent harmful operations
- All external communications (OpenAI, Jira) use secure HTTPS
- Sensitive configuration (API keys, credentials) is managed via environment variables
- Each service runs in its own container for additional isolation

## Deployment Architecture

The system is deployed using Docker Compose with three main services:

1. **API Gateway**: The main application service
2. **AI Agent**: The AI service for natural language processing
3. **Database**: The PostgreSQL database service

This containerized approach allows for:

- Easy deployment and scaling
- Isolation between components
- Consistent environments across development and production
- Simple management of dependencies

## Configuration Management

All service configurations are managed via environment variables, allowing for flexible deployment across different environments without code changes. Key configuration options include:

- Database connection parameters
- AI integration mode (direct or agent)
- OpenAI API key
- Jira integration settings
- Service URLs and ports

## Extensibility

The modular architecture facilitates easy extension of the system:

1. **Additional AI Models**: The AI Agent service can be extended to support multiple AI models or providers
2. **Database Support**: The Database Layer can be expanded to support other database systems
3. **Authentication**: Authentication mechanisms can be added to the API Gateway
4. **Caching**: Response caching can be implemented to improve performance
5. **Additional Integrations**: More data sources or context providers can be integrated alongside Jira