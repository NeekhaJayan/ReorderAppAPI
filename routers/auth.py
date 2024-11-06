
from datetime import datetime, timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request
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

class AppInstallationStatus(BaseModel):
    installed: bool

class MarkAppInstalledRequest(BaseModel):
    shop: str
    email:str

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

@router.get("/checkAppInstalled", response_model=AppInstallationStatus)
async def check_app_installed(shop: str, db: Session = Depends(get_db)):
    result = db.query(models.shops).filter((models.shops.deleted_at==None)&(models.shops.shop==shop)&(models.shops.installed==True)).all()
    print(result)
    if result:
        return {"installed": True}

    return {"installed": False}

@router.post("/markAppAsInstalled")
async def mark_app_as_installed(request: MarkAppInstalledRequest, db: Session = Depends(get_db)):

    query_model =models.shops()
    query_model.shop=request.shop
    query_model.email=request.email
    query_model.installed =True
    query_model.deleted_at=None

    db.add(query_model)
    db.commit()

    return {"message": "App marked as installed successfully"}

@router.patch("/markAppAsUnInstalled")
async def mark_app_as_uninstalled(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    shop = data.get("shop")
    
    if not shop:
        raise HTTPException(status_code=400, detail="Shop parameter is required")

    # Find the shop in the database
    query_model = db.query(models.shops).filter(
        models.shops.deleted_at == None,
        models.shops.shop == shop,
        models.shops.installed == True
    ).first()

    if not query_model:
        raise HTTPException(status_code=404, detail="Shop not found or already uninstalled")

    # Mark as uninstalled
    query_model.installed = False
    query_model.deleted_at = datetime.now()
    db.add(query_model)
    db.commit()

    return {"message": "App marked as uninstalled successfully"}