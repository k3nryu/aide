from datetime import date, datetime

from sqlalchemy import Boolean, Column, Date, DateTime, Integer, Numeric, String, Text

from database import Base


class TaskDB(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    type = Column(String(50), default="todo")  # todo / not_todo
    priority = Column(String(50), default="medium")
    done = Column(Boolean, default=False)
    due_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)


class ThoughtDB(Base):
    __tablename__ = "thoughts"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    tag = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)


class ActivityLogDB(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    category = Column(String(100))
    note = Column(Text)
    occurred_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class MoneyRecordDB(Base):
    __tablename__ = "money_records"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    type = Column(String(50), nullable=False)  # income / expense
    category = Column(String(100))
    note = Column(Text)
    record_date = Column(Date, default=date.today)
    created_at = Column(DateTime, default=datetime.utcnow)
