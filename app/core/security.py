import os

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# Configure Bearer authentication for protected API endpoints.
bearer_scheme = HTTPBearer(auto_error=False)


# Read the expected API token from the environment.
def get_api_token() -> str:
    return os.getenv("API_TOKEN", "")


# Validate the Bearer token before allowing access to protected routes.
def require_bearer_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> None:
    expected_token = get_api_token()

    # Reject requests if the server has no configured API token.
    if not expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "unauthorized",
                    "message": "Invalid bearer token",
                }
            },
        )

    # Reject requests with missing or invalid Bearer credentials.
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "unauthorized",
                    "message": "Invalid bearer token",
                }
            },
        )

    # Reject requests with an incorrect API token.
    if credentials.credentials != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "unauthorized",
                    "message": "Invalid bearer token",
                }
            },
        )