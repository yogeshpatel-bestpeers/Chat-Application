from typing import List

from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from ChatApp.Database.db import get_db
from ChatApp.models import ChatMessage, User
from ChatApp.schema import  UserGet
from ChatApp.Utils.utils import ConnectionManager

template = Jinja2Templates(directory="ChatApp/templates")
route = APIRouter()
manager = ConnectionManager()


@route.get("/{user}", response_class=HTMLResponse)
async def get(request: Request, user: str):
    return template.TemplateResponse("chat.html", {"request": request, "user": user})


@route.get("/users/get", response_model=List[UserGet])
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User.username))
    users = result.scalars().all()
    return [{"username": username} for username in users]


@route.websocket("/ws/{username}")
async def websocket_endpoint(
    username: str, websocket: WebSocket, db: AsyncSession = Depends(get_db)
):
    await manager.connect(websocket, username)
    # user1 = User(username="dev", email="ved@example.com", passwords="")
    # user2 = User(username="lockey", email="alice@example.com", passwords="")

    # db.add_all([user1, user2])

    # await db.commit()

    # Get sender user
    result = await db.execute(select(User).where(User.username == username))
    sender = result.scalar_one_or_none()

    if not sender:
        await websocket.send_text("Invalid user")
        await websocket.close(code=1008)
        return

    try:
        while True:
            data = await websocket.receive_text()
    

            if ":" not in data:
                await websocket.send_text("Invalid format. Use 'recipient: message'")
                continue

            recipient_username, message = map(str.strip, data.split(":", 1))

            # Get recipient user
            result = await db.execute(
                select(User).where(User.username == recipient_username)
            )
            recipient = result.scalar_one_or_none()

            if not recipient:
                await websocket.send_text("Recipient not found.")
                continue

            # Store message in database
            chat_message = ChatMessage(
                content=message, sender_id=sender.id, receiver_id=recipient.id
            )
            db.add(chat_message)
            await db.commit()

            # Send to both sender and receiver if connected
            formatted_msg = f"{sender.username}: {message}"
            await manager.send_private_message(
                sender.username, recipient.username, formatted_msg
            )

    except WebSocketDisconnect:
        await manager.disconnect(websocket, username)


@route.get("/chat/history/{user1}/{user2}")
async def get_chat_history(user1: str, user2: str, db: AsyncSession = Depends(get_db)):
    # Get user1 and user2
    user1 = user1.strip()
    user2 = user2.strip()
    print("----------------------debug :",user1)
    # test = await db.execute(select(User.username).where(User.username == user1))
    res1 = await db.execute(select(User).where(User.username == user1))
    res2 = await db.execute(select(User).where(User.username == user2))


    u1 = res1.scalar_one()
    print("---------------------------id is for user1",u1.id)
    u2 = res2.scalar_one()

    if not u1 or not u2:
        return []

    result = await db.execute(
        select(ChatMessage)
        .options(joinedload(ChatMessage.sender))  # Load sender info
        .where(
            or_(
                (ChatMessage.sender_id == u1.id) & (ChatMessage.receiver_id == u2.id),
                (ChatMessage.sender_id == u2.id) & (ChatMessage.receiver_id == u1.id),
            )
        )
            .order_by(ChatMessage.timestamp.asc())
        )

    messages = result.scalars().all()
    print("----------------",messages)

    return [
        {
            "content": message.content,
            "timestamp": message.timestamp,
            "sender": message.sender.username
        }
        for message in messages
    ] 
