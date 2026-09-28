from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ProviderResult:
    provider_id: str
    status: str
    metadata: dict[str, Any] = field(default_factory=dict)
    retryable: bool = False


class ProviderError(Exception):
    def __init__(self, message, *, retryable, status_code=None, safe_details=None):
        super().__init__(message)
        self.retryable = retryable
        self.status_code = status_code
        self.safe_details = safe_details or {}
