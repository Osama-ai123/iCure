from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, func, create_engine,Enum
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

DATABASE_URL = "postgresql://postgres:devpassword@localhost:5432/icure"
engine = create_engine(DATABASE_URL, echo=True)

class User(Base):
    __tablename__="users"
    id=Column(Integer,primary_key=True)
    email=Column(String(255),nullable=False,unique=True)
    pass_hash=Column(String(255),nullable=False)
    created_at=Column(DateTime,server_default=func.now())
    conversations=relationship('Conversation',back_populates='user',cascade='all,delete-orphan')


class Conversation(Base):
    __tablename__="conversations"
    id=Column(Integer,primary_key=True,)
    user_id=Column(Integer,ForeignKey(User.id,ondelete='CASCADE'),nullable=False,index=True)
    created_at=Column(DateTime,server_default=func.now())
    title=Column(String(255),nullable=True)
    user=relationship('User',back_populates='conversations')
    messages=relationship('Message',back_populates='conversation', cascade='all,delete-orphan',order_by='Message.sent_time')

class Message(Base):
    __tablename__="messages"
    id=Column(Integer,primary_key=True)
    conversation_id=Column(Integer,ForeignKey(Conversation.id,ondelete='CASCADE'),nullable=False,index=True)
    content=Column(Text,nullable=False)
    sent_time=Column(DateTime,server_default=func.now())
    role=Column(Enum("question","response",name="message_type"),nullable=False)
    conversation=relationship('Conversation',back_populates='messages')
