from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ChatApp.Database.db import Base
import uuid
from typing import List

from sqlalchemy.dialects.postgresql import UUID

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String, nullable=True)
    passwords: Mapped[str] = mapped_column(String, nullable=True, server_default="")

    sent_messages: Mapped[List["ChatMessage"]] = relationship(
        "ChatMessage", back_populates="sender", foreign_keys="ChatMessage.sender_id"
    )
    received_messages: Mapped[List["ChatMessage"]] = relationship(
        "ChatMessage", back_populates="receiver", foreign_keys="ChatMessage.receiver_id"
    )
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    content: Mapped[str] = mapped_column(String, nullable=False)
    timestamp: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    sender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    receiver_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)


    sender: Mapped["User"] = relationship("User", back_populates="sent_messages", foreign_keys=[sender_id])
    receiver: Mapped["User"] = relationship("User", back_populates="received_messages", foreign_keys=[receiver_id])