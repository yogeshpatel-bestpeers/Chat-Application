from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi_utils.cbv import cbv
from sqlalchemy.ext.asyncio import AsyncSession

from ChatApp.Database.db import get_db
from ChatApp.models import User
from ChatApp.Utils.utils import Helper

auth_router = APIRouter(tags=["Auth Api"])


@cbv(auth_router)
class AuthView:
    auth = Helper()
    db: AsyncSession = Depends(get_db)
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

    @auth_router.post("/login")
    async def login(self, form_data: OAuth2PasswordRequestForm = Depends()):
        user = await self.auth.authenticate_user(
            self.db, form_data.username, form_data.password
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials"
            )

        token = self.auth.create_access_token(data={"email": user.email})

        return {"access_token": token, "token_type": "bearer"}
