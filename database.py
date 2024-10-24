import sqlite3
# import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


SQLALCHEMY_DATABASE_URL = "postgresql://db_nursement_user:qh0pQoOXf66DK0d5LUyKSLHYYoze5xpZ@dpg-cle36h6f27hc738pm570-a.singapore-postgres.render.com/db_shopify_app_store"
engine=create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()
