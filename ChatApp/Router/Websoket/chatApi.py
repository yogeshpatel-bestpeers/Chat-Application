from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from ChatApp.models import ChatMessage, User
from ChatApp.Database.db import get_db
from ChatApp.Utils.utils import ConnectionManager  
from ChatApp.schema import UserGet


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
    return [   {
            "username": username,
        }
            for username in users]


@route.websocket("/ws/{username}")
async def websocket_endpoint(
    username: str,
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db)
):
    print("username :",username)
    await manager.connect(websocket, username)


    result = await db.execute(select(User).where(User.username == username))
    
    user = result.scalar_one_or_none()
    
    if not user :
        await websocket.send_text("Invalid user")
        await websocket.close(code=1008)
        return

    try:
        while True:
            

            data = await websocket.receive_text()

            if ":" in data:
                recipient, message = map(str.strip, data.split(":", 1))
                await manager.send_private_message(username, recipient, message)
            
            

            chat_message = ChatMessage(content=data, user_id=user.id)
            db.add(chat_message)
            await db.commit()

    except WebSocketDisconnect:
        await manager.disconnect(websocket, username)
