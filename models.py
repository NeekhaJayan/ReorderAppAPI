from sqlalchemy import  Column, Integer, String,DateTime
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class reorder(Base):
    __tablename__ = "reorder"

    reorder_id = Column(Integer, primary_key=True, index=True)
    shop= Column(String, index=True)
    email = Column(String, index=True)
    product_id = Column(Integer,  index=True)
    product_title = Column(String,  index=True)
    reorder_days = Column(Integer, index=True)
    created_date = Column(DateTime, default=datetime.utcnow)
    deleted_date = Column(DateTime, nullable=True)