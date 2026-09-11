from pydantic import BaseModel

class PublicTokenExchangeRequest(BaseModel):
    public_token: str