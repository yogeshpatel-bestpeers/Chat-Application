from pydantic import BaseModel

class UserGet(BaseModel):
    username: str

    class Config:
        orm_mode = True