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
    importance = Column(String(50), default="medium")
    urgency = Column(String(50), default="medium")
    context = Column(String(50), default="personal")  # personal / company
    todo_kind = Column(String(50), default="one_time")  # one_time / recurring
    recurrence_frequency = Column(String(50))  # daily / weekly / monthly / yearly
    recurrence_calendar = Column(String(50), default="solar")  # solar / lunar
    recurrence_month = Column(Integer)
    recurrence_day = Column(Integer)
    recurrence_weekdays = Column(String(100))
    recurrence_rule = Column(Text)
    not_todo_group = Column(String(50))
    recurrence_natural = Column(Text)
    recurrence_cron = Column(String(120))
    recurrence_prepare_days = Column(Integer)
    advanced_format = Column(String(50), default="markdown")  # markdown / yaml
    advanced_body = Column(Text)
    done = Column(Boolean, default=False)
    due_date = Column(Date)
    available_date = Column(Date)
    starts_at = Column(DateTime)
    ends_at = Column(DateTime)
    location = Column(String(255))
    source = Column(String(50), default="manual")
    completed_at = Column(DateTime)
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


class CalendarEventDB(Base):
    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    source = Column(String(50), default="manual")  # manual / google / apple / outlook
    account_context = Column(String(50), default="personal")  # personal / company
    importance = Column(String(50), default="high")
    event_kind = Column(String(50), default="one_time")  # one_time / recurring
    recurrence_frequency = Column(String(50))  # daily / weekly / monthly / yearly
    recurrence_calendar = Column(String(50), default="solar")  # solar / lunar
    recurrence_month = Column(Integer)
    recurrence_day = Column(Integer)
    recurrence_weekdays = Column(String(100))
    recurrence_natural = Column(Text)
    recurrence_rule = Column(Text)
    starts_at = Column(DateTime, nullable=False)
    ends_at = Column(DateTime)
    location = Column(String(255))
    description = Column(Text)
    external_id = Column(String(255))
    done = Column(Boolean, default=False)
    completed_at = Column(DateTime)
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
