from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class NotificationSchema(BaseModel):
    type: str = Field(..., description="Type of the notification, e.g. 'low_stock'")
    payload: Dict[str, Any] = Field(..., description="Data associated with the notification")
    timestamp: datetime = Field(default_factory=datetime.now, description="Time when the notification was created")

class LowStockPayload(BaseModel):
    product_id: int
    product_name: Optional[str] = None
    current_stock: float
    threshold: float = 2.0
    message: str