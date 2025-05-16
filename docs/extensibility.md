# Extensibility Documentation

This document describes how to extend the AI SQL Agent API with new features without affecting existing functionality.

## Adding New API Endpoints

### 1. Create a new route module

To add a new API endpoint, create a new route module in the `app/api/routes` directory:

```python
# app/api/routes/new_feature.py
from fastapi import APIRouter, Depends
from typing import List

from app.schemas.response import ResponseModel
from app.schemas.new_feature import NewFeatureRequest, NewFeatureResponse
from app.services.new_feature_service import NewFeatureService
from app.api.dependencies import get_new_feature_service

router = APIRouter()

@router.post(
    "/new-feature",
    response_model=ResponseModel[NewFeatureResponse],
    summary="Description of new feature",
    description="Detailed description of what this endpoint does"
)
async def new_feature_endpoint(
    request: NewFeatureRequest,
    new_feature_service: NewFeatureService = Depends(get_new_feature_service)
):
    result = await new_feature_service.process_request(request)
    return ResponseModel[NewFeatureResponse](
        success=True,
        data=result,
        message="Operation completed successfully"
    )
