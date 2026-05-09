from datetime import date
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import MoneyRecordDB
from schemas import MoneyCreate, MoneyOut


router = APIRouter()


@router.post("/money", response_model=MoneyOut)
def create_money_record(record: MoneyCreate, db: Session = Depends(get_db)):
    data = record.model_dump()
    if data["record_date"] is None:
        data["record_date"] = date.today()
    item = MoneyRecordDB(**data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/money", response_model=List[MoneyOut])
def list_money_records(db: Session = Depends(get_db)):
    return db.query(MoneyRecordDB).order_by(MoneyRecordDB.record_date.desc()).all()
