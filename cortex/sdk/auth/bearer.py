"""
Bearer token (JWT) authentication provider.

JWT-based authentication for modern web applications.
"""
from typing import Any, Dict, Optional

from cortex.sdk.auth.base import BaseAuthProvider
from cortex.sdk.exceptions import CortexAuthenticationError


class BearerTokenAuthProvider(BaseAuthProvider):
    """
    JWT Bearer token authentication.

    Validates JWT tokens and extracts payload as auth context.

    Attributes:
        secret_key: Secret key for JWT validation
        algorithm: JWT algorithm (default: HS256)
        audience: Optional audience claim to validate
        issuer: Optional issuer claim to validate

    Examples:
        Basic usage:
        >>> provider = BearerTokenAuthProvider(secret_key="my-secret")
        >>> context = provider.authenticate({"bearer_token": "eyJ..."})
        >>> print(context["user_id"])

        With audience and issuer validation:
        >>> provider = BearerTokenAuthProvider(
        ...     secret_key="my-secret",
        ...     algorithm="HS256",
        ...     audience="cortex-api",
        ...     issuer="https://auth.example.com"
        ... )
    """

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        audience: Optional[str] = None,
        issuer: Optional[str] = None,
    ):
        """
        Initialize Bearer token provider.

        Args:
            secret_key: Secret key for JWT validation
            algorithm: JWT algorithm (default: HS256)
            audience: Optional audience claim to validate
            issuer: Optional issuer claim to validate

        Examples:
            >>> provider = BearerTokenAuthProvider(secret_key="secret")
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.audience = audience
        self.issuer = issuer

    def authenticate(self, credentials: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Authenticate using Bearer token (JWT).

        Args:
            credentials: Dict containing "bearer_token"

        Returns:
            JWT payload as auth context

        Raises:
            CortexAuthenticationError: If token missing or invalid

        Examples:
            >>> provider = BearerTokenAuthProvider(secret_key="secret")
            >>> context = provider.authenticate({"bearer_token": "eyJ..."})
        """
        token = credentials.get("bearer_token")
        if not token:
            raise CortexAuthenticationError("Bearer token required")

        try:
            import jwt

            # Build decode options
            decode_options = {
                "verify_signature": True,
            }

            decode_kwargs = {}
            if self.audience:
                decode_kwargs["audience"] = self.audience
            if self.issuer:
                decode_kwargs["issuer"] = self.issuer

            # Decode and validate token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                **decode_kwargs,
            )

            return payload

        except jwt.InvalidTokenError as e:
            raise CortexAuthenticationError(f"Invalid token: {e}")
        except ImportError:
            raise CortexAuthenticationError(
                "PyJWT library required for Bearer token authentication. "
                "Install with: pip install PyJWT"
            )
