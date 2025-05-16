# AI SQL Agent - Extensibility Guide

This guide provides instructions on how to extend the AI SQL Agent system with new features, integrations, or modifications without affecting existing functionality.

## Modular Architecture

The AI SQL Agent is designed with a highly modular architecture to facilitate easy extension:

- **API Gateway**: Main application with clear separation of routes and services
- **AI Agent Service**: Separate container for AI operations
- **Database Layer**: Abstracted database access with clear interfaces
- **Jira Integration**: Modular integration with external system

Each component can be extended independently without affecting the others, as long as their interfaces remain compatible.

## Adding New API Endpoints

### Step 1: Create a New Route Module

Create a new route file in the appropriate location, such as `routes/new_feature.py`:

```python
from flask import Blueprint, request, jsonify

# Create a blueprint for the new feature
new_feature_bp = Blueprint('new_feature', __name__)

@new_feature_bp.route('/api/new-feature', methods=['GET'])
def get_new_feature():
    """Implement your new feature here"""
    # Implementation...
    return jsonify({
        'success': True,
        'data': { /* your data */ },
        'message': 'New feature executed successfully'
    })
```

### Step 2: Register the Blueprint

Register your new blueprint in the main application:

```python
from routes.new_feature import new_feature_bp

# Register the new blueprint
app.register_blueprint(new_feature_bp)
```

## Adding New AI Models or Providers

The system supports two AI integration modes: direct OpenAI integration and a separate AI Agent service. You can extend either approach to support additional AI models or providers.

### Extending Direct Integration

1. Create a new service class for the AI provider:

```python
class NewAIProviderService:
    """
    Service for interacting with a new AI provider.
    """
    def __init__(self):
        # Initialize the service...
        
    async def generate_sql(self, query, schema_info, jira_context=None, additional_context=None):
        # Implement SQL generation using the new AI provider...
        
    async def explain_results(self, query, sql, results, jira_context=None):
        # Implement results explanation using the new AI provider...
```

2. Update the configuration to support the new provider:

```python
# In config.py
AI_PROVIDER = os.environ.get("AI_PROVIDER", "openai")  # Options: "openai", "new_provider"
```

3. Update the gateway to use the appropriate service based on configuration:

```python
if Config.AI_PROVIDER == "openai":
    # Use OpenAI service
    # ...
elif Config.AI_PROVIDER == "new_provider":
    # Use new provider service
    # ...
```

### Extending the AI Agent Service

1. Add support for new models in the AI Agent service:

```python
# In AI Agent's main.py
MODEL_PROVIDER = os.environ.get("MODEL_PROVIDER", "openai")

@app.post("/generate-sql")
async def generate_sql(request: NLQueryRequest):
    if MODEL_PROVIDER == "openai":
        # Use OpenAI for generation
        # ...
    elif MODEL_PROVIDER == "new_provider":
        # Use new provider for generation
        # ...
```

2. Update the AI Agent's Dockerfile to include any new dependencies required by the new provider.

## Adding New Database Support

The system is designed to work with PostgreSQL by default, but you can extend it to support other database systems.

1. Create a new database connector class:

```python
class NewDatabaseConnection:
    """
    Database connection manager for a new database system.
    """
    def __init__(self):
        # Initialize connection...
        
    def get_connection(self):
        # Get a database connection...
        
    def execute_query(self, sql):
        # Execute a query...
        
    def get_schema_info(self):
        # Retrieve schema information...
```

2. Update the configuration to support multiple database types:

```python
# In config.py
DATABASE_TYPE = os.environ.get("DATABASE_TYPE", "postgresql")  # Options: "postgresql", "new_database"
```

3. Update the database initialization in the application:

```python
if Config.DATABASE_TYPE == "postgresql":
    db_connection = PostgreSQLConnection()
elif Config.DATABASE_TYPE == "new_database":
    db_connection = NewDatabaseConnection()
```

## Adding Authentication

The system currently does not implement authentication, but you can add it as follows:

1. Create an authentication module:

```python
from flask import request, jsonify
from functools import wraps

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({
                'success': False,
                'message': 'Authentication token is missing'
            }), 401
            
        # Verify the token...
        
        return f(*args, **kwargs)
    
    return decorated
```

2. Use the decorator with your routes:

```python
@gateway_bp.route('/api/sql/generate', methods=['POST'])
@token_required
def generate_sql():
    # Implementation...
```

## Adding Caching

To improve performance, you can add caching for frequent or expensive operations:

1. Set up a caching layer:

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_cached_schema_info():
    """Cached version of schema retrieval"""
    return db_connection.get_schema_info()
```

2. Use the cached function where appropriate:

```python
# Instead of:
# schema_info = db_connection.get_schema_info()

# Use:
schema_info = get_cached_schema_info()
```

## Adding New External Integrations

Beyond Jira, you can integrate with other external systems:

1. Create a service class for the integration:

```python
class NewIntegrationService:
    """
    Service for integrating with a new external system.
    """
    def __init__(self):
        # Initialize the service...
        
    async def get_context(self, resource_id):
        # Retrieve context from the external system...
```

2. Add appropriate routes for the integration:

```python
@gateway_bp.route('/api/new-integration/<resource_id>', methods=['GET'])
def get_integration_context(resource_id):
    # Use the integration service...
```

## Extending the Front-end

The current system provides a basic front-end with the static HTML file. You can extend it by:

1. Creating a more sophisticated front-end using a framework (React, Vue, etc.)
2. Building a separate front-end application that communicates with the API
3. Adding visualization components for SQL results using libraries like Chart.js

## Best Practices for Extensions

1. **Maintain Backward Compatibility**: Ensure your extensions don't break existing functionality
2. **Follow the Design Pattern**: Use the same patterns and structures as the existing code
3. **Add Tests**: Write unit and integration tests for your extensions
4. **Document Changes**: Update documentation to reflect your extensions
5. **Use Environment Variables**: Configure your extensions using environment variables
6. **Implement Feature Flags**: Use feature flags to enable/disable extensions
7. **Follow API Standards**: Maintain consistent API response formats

## Example: Adding Support for Azure OpenAI Service

Here's a complete example of adding support for Azure OpenAI Service:

1. Update `openai_service.py`:

```python
class AzureOpenAIService:
    """
    Service for Azure OpenAI API integration.
    """
    def __init__(self):
        self.api_key = os.environ.get("AZURE_OPENAI_API_KEY")
        self.endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        self.deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT")
        self.is_configured = all([self.api_key, self.endpoint, self.deployment])
        
        if not self.is_configured:
            logging.warning("Azure OpenAI service not configured with valid credentials")
        
        # Initialize Azure OpenAI client
        self.client = openai.AzureOpenAI(
            api_key=self.api_key,
            api_version="2023-05-15",
            azure_endpoint=self.endpoint
        ) if self.is_configured else None
    
    async def generate_sql(self, query, schema_info, jira_context=None, additional_context=None):
        # Implementation similar to the OpenAI service but using Azure-specific client...

    async def explain_results(self, query, sql, results, jira_context=None):
        # Implementation similar to the OpenAI service but using Azure-specific client...
```

2. Update `config.py`:

```python
# AI provider options
AI_PROVIDER = os.environ.get("AI_PROVIDER", "openai")  # Options: "openai", "azure"
```

3. Update the gateway to use the appropriate service:

```python
if Config.AI_PROVIDER == "openai":
    ai_service = OpenAIService()
elif Config.AI_PROVIDER == "azure":
    ai_service = AzureOpenAIService()
else:
    logger.error(f"Unsupported AI provider: {Config.AI_PROVIDER}")
    ai_service = None
```

4. Update documentation to reflect the new option:

```markdown
| Variable | Description | Default | Options |
|----------|-------------|---------|---------|
| AI_PROVIDER | The AI provider to use | openai | openai, azure |
| AZURE_OPENAI_API_KEY | Azure OpenAI API key | - | Required for Azure |
| AZURE_OPENAI_ENDPOINT | Azure OpenAI endpoint | - | Required for Azure |
| AZURE_OPENAI_DEPLOYMENT | Azure OpenAI deployment | - | Required for Azure |
```

This approach maintains backward compatibility while adding support for a new AI provider.