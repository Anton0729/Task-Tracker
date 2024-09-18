from pydantic import BaseModel


class Token(BaseModel):
    access_toke: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None
