from datetime import datetime
from typing import Optional
from app.core.logging import get_logger

logger = get_logger(__name__)


class AuditStore:
    def __init__(self):
        self.entries: list[dict] = []

    def log(self, event_type: str, user_id: str = "anonymous", tenant_id: str = "default", details: dict | None = None):
        entry = {
            "event_type": event_type,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "timestamp": datetime.now().isoformat(),
            "details": details or {},
        }
        self.entries.append(entry)
        logger.info(f"Audit: {event_type} by {user_id}")

    def get_entries(self, event_type: Optional[str] = None, limit: int = 100) -> list[dict]:
        entries = self.entries
        if event_type:
            entries = [e for e in entries if e["event_type"] == event_type]
        return entries[-limit:]


audit_store = AuditStore()
