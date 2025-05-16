# AI SQL Agent API

A FastAPI backend application with AI SQL agents, Jira integration, and comprehensive features for translating natural language queries into SQL and executing them.

## Features

- **AI SQL Agent**: Convert natural language queries to SQL using OpenAI's GPT models
- **Jira Integration**: Extract context from Jira issues to enhance SQL queries
- **Standard Backend Features**:
  - Comprehensive logging system
  - CORS middleware
  - Rate limiting
  - Swagger documentation
  - Error handling

## Architecture

The system consists of the following major components:

1. **FastAPI Backend**: Handles HTTP requests and responses
2. **AI SQL Agent**: Converts natural language to SQL using LLMs
3. **Jira Integration**: Fetches and processes Jira issues for context
4. **Database Connector**: Executes SQL queries against the database

See the [architecture documentation](docs/architecture.md) for more details.

## Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL database
- OpenAI API key
- Jira API credentials (optional)

### Environment Variables

The application requires the following environment variables:

