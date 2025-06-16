from datetime import datetime

from pydantic import BaseModel


class UserGet(BaseModel):
    username: str

    class Config:
        orm_mode = True


class ChatMessageSchema(BaseModel):

    content: str
    timestamp: datetime
    sender_id: int
    receiver_id: int

    class Config:
        orm_mode = True
