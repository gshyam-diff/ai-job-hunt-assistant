"""
Security utilities for safe logging and secret handling.
Use these instead of printing secrets directly.
"""


def mask_secret(secret: str, show_prefix: int = 10, show_suffix: int = 4) -> str:
    """
    Mask a secret string, showing only prefix and suffix.

    Args:
        secret: The secret string to mask
        show_prefix: Number of characters to show at the start
        show_suffix: Number of characters to show at the end

    Returns:
        Masked string like "sk-ant-api03-...qwAA"

    Examples:
        >>> mask_secret("sk-ant-abcd1234efgh5678ijkl", 10, 4)
        'sk-ant-abc...ijkl'
    """
    if not secret:
        return "[REDACTED]"

    if len(secret) < show_prefix + show_suffix + 3:
        return "[REDACTED]"

    return f"{secret[:show_prefix]}...{secret[-show_suffix:]}"


def is_secret_set(secret: str) -> bool:
    """
    Check if a secret is set (safe to use in logs).

    Args:
        secret: The secret string to check

    Returns:
        True if secret is set and non-empty

    Example:
        >>> api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        >>> print(f"API key available: {is_secret_set(api_key)}")
        API key available: True
    """
    return bool(secret and len(secret) > 0)


def log_secret_status(secret_name: str, secret_value: str) -> str:
    """
    Generate a safe log message for secret status.

    Args:
        secret_name: Name of the secret (e.g., "ANTHROPIC_API_KEY")
        secret_value: The actual secret value

    Returns:
        Safe log message

    Example:
        >>> api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        >>> print(log_secret_status("ANTHROPIC_API_KEY", api_key))
        ✓ ANTHROPIC_API_KEY loaded: sk-ant-api03-...qwAA (length: 126)
    """
    if not is_secret_set(secret_value):
        return f"⚠️  {secret_name} is NOT set"

    masked = mask_secret(secret_value)
    length = len(secret_value)
    return f"✓ {secret_name} loaded: {masked} (length: {length})"


def sanitize_error(error: Exception, expose_message: bool = True) -> str:
    """
    Create a safe error message that doesn't expose secrets.

    Args:
        error: The exception to sanitize
        expose_message: Whether to include the error message (safe ones only)

    Returns:
        Safe error description

    Example:
        >>> try:
        >>>     api_call()
        >>> except Exception as e:
        >>>     print(sanitize_error(e))
        anthropic.RateLimitError: Too many requests
    """
    error_type = type(error).__name__
    error_msg = str(error)

    # Don't expose certain sensitive error details
    if "api_key" in error_msg.lower() or "token" in error_msg.lower():
        return f"{error_type}: Authentication error"

    if expose_message:
        return f"{error_type}: {error_msg}"
    else:
        return error_type
