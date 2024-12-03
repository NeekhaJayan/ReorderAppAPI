
from datetime import datetime, timedelta
from typing import Annotated, List
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request
import models
from models import Products,Shop,Orders,ShopCustomer,OrderProduct,Reminder
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

class UpdateProduct(BaseModel):
    shopify_product_id: str
    reorder_days: int

class ShopCreate(BaseModel):
    shopify_domain: str
    shop_name: str = None
    shop_logo: str = None  # Optional field
    email: EmailStr =None # Ensures email is valid
    message_template_id: int = None 

class LineItem(BaseModel):
    product_id: int
    varient_id:int
    quantity: int
    status:str
    price: str

class OrderPayload(BaseModel):
    shop:str
    shopify_order_id: int
    customer_id: int
    customer_email: str
    customer_name: str
    customer_phone: str
    shipping_phone:str
    billing_phone:str
    line_items: List[LineItem]
    order_date: str

@router.get("/products/", response_model=List[dict])
def get_products( db: Session = Depends(get_db)):
    """
    Get all products or filter by `shop_id`.

    Args:
    - shop_id (Optional[int]): The ID of the shop to filter products.
    - db (Session): The database session.

    Returns:
    - List of products or filtered products.
    """
    try:
        # Query all products if no `shop_id` is provided
        # if shop_id:
        #     products = db.query(Products).filter(Products.shop_id == shop_id).all()
        # else:
        products = db.query(Products).all()
        
        # if not products:
        #     raise HTTPException(status_code=404, detail="No products found.")
        
        # Convert products to dictionaries for response
        product_list = [
            {
                "product_id": product.product_id,
                "shop_id": product.shop_id,
                "shopify_product_id": product.shopify_product_id,
                "title": product.title,
                "reorder_days": product.reorder_days,
                "created_at":product.created_at,
            }
            for product in products
        ]
        
        return product_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching products: {e}")

    
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

@router.patch("/products/{product_id}", response_model=dict)
def update_product(
    product_id: int,
    product: UpdateProduct,
    db: Session = Depends(get_db)
):
    # Fetch the existing product by product_id
    
    existing_product = db.query(Products).filter(Products.shopify_product_id == product_id).first()
    
    if not existing_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if product.shopify_product_id is not None:
        existing_product.shopify_product_id = product.shopify_product_id

    if product.reorder_days is not None:
        existing_product.reorder_days = product.reorder_days

    # Optionally update a modified timestamp (if your model supports it)
    # existing_product.modified_at = datetime.utcnow()

    try:
        # Commit the changes to the database
        db.commit()
        db.refresh(existing_product)  # Refresh to get the updated data
        return {"message": "Product updated successfully", "product_id": existing_product.product_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating product: {e}")

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

@router.get("/shops/{shop_domain}", response_model=dict)
def get_shop(shop_domain: str, db: Session = Depends(get_db)):
    # Query the database for the shop by shop_id
    shop = db.query(Shop).filter(Shop.shopify_domain == shop_domain).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    # Return shop details
    return {
        "shop_id": shop.shop_id,
    }

@router.patch("/shops/{shop_id}", response_model=dict)
def update_shop(
    shop_id: int,
    shop: ShopCreate,
    db: Session = Depends(get_db)
):
    # Fetch the existing shop by shop_id
    existing_shop = db.query(Shop).filter(Shop.shop_id == shop_id).first()
    
    if not existing_shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    # Update only the fields that are provided
    if shop.shop_name:
        existing_shop.shop_name = shop.shop_name
    if shop.shopify_domain:
        existing_shop.shopify_domain = shop.shopify_domain
    if shop.shop_logo:
        existing_shop.shop_logo = shop.shop_logo
    if shop.email:
        existing_shop.email = shop.email
    if shop.message_template_id:
        existing_shop.message_template_id = shop.message_template_id
    
    # Update the modified timestamp
    existing_shop.modified_at = datetime.utcnow()

    # Commit the changes to the database
    db.commit()
    db.refresh(existing_shop)

    return {"message": "Shop updated successfully", "shop_id": existing_shop.shop_id}


@router.post("/webhook/orderfullfilled")
async def receive_order(order: OrderPayload, db: Session = Depends(get_db)):
    try:
    # Process the order payload
        print(f"Received order: {order}")
        shop = db.query(Shop).filter(Shop.shopify_domain == order.shop).first()
        if not shop:
            raise HTTPException(status_code=404, detail="Shop not found")
        
        customer=ShopCustomer(
            shopify_id=order.customer_id,
            email=order.customer_email,
            mobile=order.customer_phone,
            first_name=order.customer_name,
            billing_mobile_no=order.billing_phone,
            shipping_mobile_no=order.shipping_phone
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        for line_item in order.line_items:
            # Check product in database
            product = db.query(Products).filter(Products.shopify_product_id == line_item.product_id).first()
            if not product:
                pass

            # Add the order
            new_order = Orders(
                shop_id=shop.shop_id,
                shopify_order_id=order.order_id,
                customer_id=customer.shop_customer_id,
                order_date=datetime.strptime(order.order_date, "%Y-%m-%dT%H:%M:%S"),  # Ensure datetime conversion
                total_amount=line_item.price,
                status=line_item.status,  # Ensure 'status' exists in line_item
            )
            db.add(new_order)
            db.commit()
            db.refresh(new_order)

            # Add the order product
            new_order_product = OrderProduct(
                order_id=new_order.order_id,
                shopify_product_id=line_item.product_id,
                quantity=line_item.quantity,
                shopify_varient_id=line_item.varient_id,
            )
            db.add(new_order_product)
            db.commit()
            db.refresh(new_order_product)

            # Add reminder entry
            reminder_date = new_order.order_date + timedelta(days=product.reorder_days)
            create_reminder_entry = Reminder(
                customer_id=customer.shop_customer_id,
                product_id=product.product_id,
                order_id=new_order.order_id,
                reminder_date=reminder_date,
            )
            db.add(create_reminder_entry)
            db.commit()
            db.refresh(create_reminder_entry)

        
        # Add the new product to the database
          # Refresh to get the ID
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating product: {e}")

    return {"message": "Order received successfully", "order": order}