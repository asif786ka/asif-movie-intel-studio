import re
import time
from typing import Optional
from collections import defaultdict
from fastapi import Request, HTTPException
from app.core.logging import get_logger

logger = get_logger(__name__)

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"ignore\s+(all\s+)?above\s+instructions",
    r"disregard\s+(all\s+)?previous",
    r"forget\s+(all\s+)?(your\s+)?instructions",
    r"you\s+are\s+now\s+a",
    r"new\s+instruction[s]?\s*:",
    r"system\s*:\s*you\s+are",
    r"<\s*system\s*>",
    r"\[\s*SYSTEM\s*\]",
    r"pretend\s+you\s+are",
    r"act\s+as\s+if\s+you",
    r"override\s+(your\s+)?instructions",
    r"reveal\s+(your\s+)?(system\s+)?prompt",
    r"what\s+(is|are)\s+your\s+(system\s+)?instructions",
]

_compiled_patterns = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


def detect_prompt_injection(text: str) -> tuple[bool, Optional[str]]:
    for pattern in _compiled_patterns:
        match = pattern.search(text)
        if match:
            logger.warning(f"Prompt injection detected: {match.group()}")
            return True, match.group()
    return False, None


ALLOWED_UPLOAD_TYPES = {".txt", ".md", ".pdf", ".png", ".jpg", ".jpeg"}
MAX_FILENAME_LENGTH = 255


def validate_file_upload(filename: str, file_size: int, max_size_mb: int = 50) -> tuple[bool, Optional[str]]:
    if not filename or len(filename) > MAX_FILENAME_LENGTH:
        return False, "Invalid filename"

    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_UPLOAD_TYPES:
        return False, f"File type '{ext}' not allowed. Allowed: {ALLOWED_UPLOAD_TYPES}"

    max_bytes = max_size_mb * 1024 * 1024
    if file_size > max_bytes:
        return False, f"File too large. Max: {max_size_mb}MB"

    return True, None


class RateLimiter:
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def check(self, client_id: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds
        self._requests[client_id] = [
            t for t in self._requests[client_id] if t > window_start
        ]
        if len(self._requests[client_id]) >= self.max_requests:
            return False
        self._requests[client_id].append(now)
        return True


rate_limiter = RateLimiter()


async def jwt_auth_scaffold(request: Request) -> Optional[dict]:
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None
    return {"user_id": "demo_user", "tenant_id": "default"}


def get_tenant_id(request: Request) -> str:
    return request.headers.get("X-Tenant-ID", "default")
