
from datetime import datetime, timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request
import models
from models import Products,Shop
from sqlalchemy.orm import Session
from database import engine ,get_db
from pydantic import BaseModel, EmailStr



router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={401: {"user": "Not authorized"},500:{"user":"Internal Server Error"},400:{"user":"Invalid Request"}}
)

models.Base.metadata.create_all(bind=engine)
db_dependency=Annotated[Session,Depends(get_db)]


class ProductCreate(BaseModel):
    shop_id: int
    shopify_product_id: str
    title: str
    reorder_days: int

class ShopCreate(BaseModel):
    shopify_domain: str
    shop_name: str = None
    shop_logo: str = None  # Optional field
    email: EmailStr =None # Ensures email is valid
    message_template_id: int = None 

    
@router.post("/products/", response_model=dict)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    # Create a new product instance
    new_product = Products(
        shop_id=product.shop_id,
        shopify_product_id=product.shopify_product_id,
        title=product.title,
        reorder_days=product.reorder_days,
    )
    try:
        # Add the new product to the database
        db.add(new_product)
        db.commit()
        db.refresh(new_product)  # Refresh to get the ID
        return {"message": "Product created successfully", "product_id": new_product.product_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating product: {e}")


@router.post("/shops/", response_model=dict)
def create_shop(shop: ShopCreate, db: Session = Depends(get_db)):
    # Check if shop already exists by domain or email
    existing_shop = db.query(Shop).filter(
        (Shop.shopify_domain == shop.shopify_domain) | (Shop.email == shop.email)
    ).first()
    if existing_shop:
        return {"message": "Shop Already Created", "shop_id": existing_shop.shop_id}
    
    # Create a new Shop instance
    new_shop = Shop(
        shopify_domain=shop.shopify_domain,
        shop_name=shop.shop_name,
        shop_logo=shop.shop_logo,
        email=shop.email,
        message_template_id=shop.message_template_id,
        created_at=datetime.utcnow(),
        modified_at=datetime.utcnow(),
    )
    db.add(new_shop)
    db.commit()
    db.refresh(new_shop)
    return {"message": "Shop created successfully", "shop_id": new_shop.shop_id}