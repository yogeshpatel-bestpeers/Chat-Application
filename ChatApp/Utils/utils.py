from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, Request, WebSocket, status
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ChatApp.models import User
from ChatApp.settings.config import get_settings

settings = get_settings()


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, username: str):
        await websocket.accept()
        self.active_connections[username] = websocket

    async def disconnect(self, websocket: WebSocket, username: str):
        if username in self.active_connections:
            del self.active_connections[username]

    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)

    async def send_private_message(self, sender: str, recipient: str, message: str):
        recipient_ws = self.active_connections.get(recipient)
        sender_ws = self.active_connections.get(sender)

        if recipient_ws:
            await recipient_ws.send_json(
                {"type": "chat", "user": sender, "message": message}
            )

        if sender_ws:
            await sender_ws.send_json(
                {"type": "chat", "user": sender, "message": message}
            )

        if not recipient_ws and sender_ws:
            await sender_ws.send_json(
                {"type": "system", "message": f"User '{recipient}' is not online."}
            )


class Helper:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.SECRET_KEY = settings.SECRET_KEY
        self.ALGORITHM = settings.ALGORITHM
        self.ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    def hash_password(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, data: dict, expires_delta: timedelta = None) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (
            expires_delta or timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

    async def authenticate_user(self, db: AsyncSession, email: str, password: str):
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        if not user or not self.verify_password(password, user.passwords):
            return None
        return user

    async def get_current_user(self, token: str, db: AsyncSession):

        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            email: str = payload.get("email")

            if email is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload",
                )

            result = await db.execute(select(User).where(User.email == email))
            user = result.scalars().first()

            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=f"User Not Found"
                )
            return user

        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired or Invalid",
            )
