from datetime import datetime

from pydantic import BaseModel, ConfigDict

class UserResponse(BaseModel):
    id: int
    email: str
    first_name: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True,)