from fastapi import status

class AppException(Exception):
    """
    Base exception class for application-specific exceptions.
    """
    def __init__(self, detail: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.detail = detail
        self.status_code = status_code
        super().__init__(self.detail)

class ValidationError(AppException):
    """
    Exception for validation errors.
    """
    def __init__(self, detail: str):
        super().__init__(detail, status_code=status.HTTP_400_BAD_REQUEST)

class NotFoundError(AppException):
    """
    Exception for resources that are not found.
    """
    def __init__(self, detail: str):
        super().__init__(detail, status_code=status.HTTP_404_NOT_FOUND)

class AuthenticationError(AppException):
    """
    Exception for authentication errors.
    """
    def __init__(self, detail: str):
        super().__init__(detail, status_code=status.HTTP_401_UNAUTHORIZED)

class RateLimitExceededError(AppException):
    """
    Exception for rate limit exceeded errors.
    """
    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(detail, status_code=status.HTTP_429_TOO_MANY_REQUESTS)

class ExternalServiceError(AppException):
    """
    Exception for errors with external services (Jira, OpenAI).
    """
    def __init__(self, detail: str, service_name: str):
        message = f"{service_name} service error: {detail}"
        super().__init__(message, status_code=status.HTTP_502_BAD_GATEWAY)

class DatabaseError(AppException):
    """
    Exception for database errors.
    """
    def __init__(self, detail: str):
        super().__init__(detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
