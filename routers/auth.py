
from datetime import datetime, timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, FastAPI, Query, Request
import models
from sqlalchemy.orm import Session
from database import engine ,get_db
from pydantic import BaseModel



router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={401: {"user": "Not authorized"},500:{"user":"Internal Server Error"},400:{"user":"Invalid Request"}}
)

models.Base.metadata.create_all(bind=engine)
db_dependency=Annotated[Session,Depends(get_db)]


class Reorder(BaseModel):

    shop: str
    email: str
    product_id: str
    product_title:str
    reorder_days: int

class Edit_Reorder(BaseModel):
    product_id: str
    reorder_days: int


@router.get('/reorder_details')
async def get_reorder_detail(request: Request,db: Session = Depends(get_db)):

    getProductData_model=db.query(models.reorder).filter(models.reorder.deleted_date==None).all()
    productData=[]
    for row in getProductData_model:
        product={
            "reorderid":row.reorder_id,
            "productId":row.product_id,
            "productTitle":row.product_title,
            "reorder_days":row.reorder_days,
            "created_at":row.created_date,
        }
        productData.append(product)
    return productData


@router.post("/reorder")
async def create_reorder(reorder: Reorder,db: Session = Depends(get_db)):
    # reorder_date = datetime.now() + datetime.timedelta(days=reorder.reorder_days)
    query_model =models.reorder()
    query_model.shop=reorder.shop
    query_model.email=reorder.email
    query_model.product_id=reorder.product_id
    query_model.product_title=reorder.product_title
    query_model.reorder_days=reorder.reorder_days

    db.add(query_model)
    db.commit()
    reorderDetails=[{
            "reorderid":query_model.reorder_id,
            "productId":query_model.product_id,
            "productTitle":query_model.product_title,
            "reorder_days":query_model.reorder_days,
            "created_at":query_model.created_date,
        }]
    return reorderDetails

@router.patch("/reorder/{productId}")
async def edit_reorder(reorder: Edit_Reorder,productId:str,db: Session = Depends(get_db)):

    db.query(models.reorder).filter(models.reorder.product_id==productId).update({"reorder_days":reorder.reorder_days})
    db.commit()
    return {"message": "Updated successfully"}