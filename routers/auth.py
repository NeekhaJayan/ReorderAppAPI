
from datetime import timedelta
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, FastAPI, File, Form, HTTPException, Query, Request, UploadFile
import models
# import requests
from models import Products,Shop,Orders,ShopCustomer,OrderProduct,Reminder,Message_Template
from dependencies import get_s3_client,AWS_BUCKET,AWS_REGION_NAME
from sqlalchemy.orm import Session
from database import engine ,get_db
from pydantic import BaseModel, EmailStr
# from pydantic_settings import BaseSettings
from datetime import datetime
import pytz
from dateutil import parser
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
import os
from botocore.client import BaseClient

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={401: {"user": "Not authorized"},500:{"user":"Internal Server Error"},400:{"user":"Invalid Request"}}
)

models.Base.metadata.create_all(bind=engine)
db_dependency=Annotated[Session,Depends(get_db)]

API_KEY=os.getenv("SENDINBLUE_API_KEY")
# class ShopifySettings(BaseSettings):
#     api_version: str = "2023-04"
#     shop_name: str  # Shopify shop name
#     access_token: str  # Shopify access token (optional if provided dynamically)

#     class Config:
#         env_file = ".env"

# def get_shopify_settings() -> ShopifySettings:
#     return ShopifySettings()

# class ShopifyService:
#     def __init__(self, settings: ShopifySettings):
#         self.settings = settings
#         self.base_url = f"https://{settings.shop_name}.myshopify.com/admin/api/{settings.api_version}"

    # def get_shop_domain(self):
    #     url = f"{self.base_url}/shop.json"
    #     headers = {"X-Shopify-Access-Token": self.settings.access_token}

    #     response = requests.get(url, headers=headers)
    #     if response.status_code != 200:
    #         raise HTTPException(
    #             status_code=response.status_code,
    #             detail=f"Error fetching shop domain: {response.json().get('errors', 'Unknown error')}",
    #         )
        
    #     return response.json()["shop"]["myshopify_domain"]

class ProductCreate(BaseModel):
    shop_id: int
    shopify_product_id: str
    title: str
    reorder_days: int

class UpdateProduct(BaseModel):
    shopify_product_id: str
    reorder_days: Optional[int] = None

class ShopCreate(BaseModel):
    shopify_domain: str
    shop_name: Optional[str] = None
    shop_logo: Optional[str] = None  # Optional field
    email: Optional[EmailStr] = None # Ensures email is valid
    message_template_id: Optional[int] = None

class LineItem(BaseModel):
    product_id: int
    varient_id: Optional[int] = None
    quantity: int
    status:str
    price: str

class OrderPayload(BaseModel):
    shop:str
    shopify_order_id: int
    customer_id: int
    customer_email: str
    customer_name: str
    customer_phone: Optional[str] = None
    shipping_phone:Optional[str] = None
    billing_phone:Optional[str] = None
    line_items: List[LineItem]
    order_date: str

class GeneralSettings(BaseModel):
    shop_name:str
    tab: str

    
    

class EmailTemplateSettings(BaseModel):
    shop_name:str
    tab: str
    # reminderEmailsEnabled:bool
    mail_server: str
    port: str
    subject: str
    fromName: EmailStr
    coupon: Optional[str] = None
    discountPercent: Optional[str] = None
    bufferTime: Optional[int] = None


HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>Reorder Reminder</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      margin: 0;
      padding: 0;
      background-color: #f9fafb;
      color: #202223;
    }}
    .email-container {{
      max-width: 600px;
      margin: 40px auto;
      background: #ffffff;
      border: 1px solid #dbe1e6;
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }}
    .header {{
      background-color: #007ace;
      text-align: center;
      padding: 20px;
      color: white;
    }}
    .content {{
      padding: 20px;
    }}
    .product-section {{
      text-align: center;
      margin: 20px 0;
    }}
    .cta {{
      text-align: center;
      margin: 20px 0;
    }}
    .cta a {{
      text-decoration: none;
      color: white;
      background-color: #007ace;
      padding: 10px 20px;
      border-radius: 4px;
    }}
    .coupon {{
      text-align: center;
      margin: 10px 0;
      font-size: 14px;
      background-color: #eef4fb;
      color: #007ace;
      padding: 10px;
      border-radius: 4px;
    }}
    .footer {{
      text-align: center;
      padding: 10px;
      font-size: 12px;
      color: #8c9196;
    }}
  </style>
</head>
<body>
  <div class="email-container">
    <div class="header">
      <h1>Your Shop</h1>
    </div>
    <div class="content">
      <p>Hello {first_name},</p>
      <p>Your <strong>{product_name}</strong> might be running low. Don't worry – you can reorder with just one click!</p>
      <div class="product-section">
        <img src="{product_image}" alt="{product_name}" />
        <p><strong>Product Name:</strong> {product_name}</p>
        <p><strong>Quantity Ordered:</strong> {quantity}</p>
        <p><strong>Estimated Days Remaining:</strong> {remaining_days}</p>
      </div>
      <div class="cta">
        <a href="{reorder_url}" target="_blank">Reorder Now and Save 10%</a>
      </div>
      <div class="coupon">
        Use code <strong>RESTOCK10</strong> at checkout to save 10% on your reorder.
      </div>
    </div>
    <div class="footer">
      <p>Powered by ReOrder Reminder Pro</p>
      <p>Need help? <a href="mailto:support@yourstore.com">support@yourstore.com</a></p>
    </div>
  </div>
</body>
</html>
"""

from fastapi import FastAPI, Depends

app = FastAPI()

# @router.get("/shop-domain")
# def get_shop_domain(shopify_settings: ShopifySettings = Depends(get_shopify_settings),db: Session = Depends(get_db)):
#     shopify_service = ShopifyService(shopify_settings)
#     shop_domain = shopify_service.get_shop_domain()
#     shop = db.query(Shop).filter(Shop.shopify_domain == shop_domain).first()
#     if not shop:
#         raise HTTPException(status_code=404, detail="Shop not found")
#     return {"shop_id": shop.shop_id}


@router.get("/products/{shop_id}", response_model=List[dict])
def get_products(shop_id:int, db: Session = Depends(get_db)):
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
        products = db.query(Products).filter((Products.shop_id == shop_id )&(Products.is_deleted == False)).all()
        # products = db.query(Products).all()
        
        if not products:
            raise HTTPException(status_code=404, detail="No products found.")
        
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
        db.refresh(new_product) 
        reorderDetails=[{
                "product_id": new_product.product_id,
                "shop_id": new_product.shop_id,
                "shopify_product_id": new_product.shopify_product_id,
                "title": new_product.title,
                "reorder_days": new_product.reorder_days,
                "created_at":new_product.created_at,
        }] # Refresh to get the ID
        return reorderDetails
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
        existing_product.reorder_days = product.reorder_days

        if product.reorder_days is  None:
            existing_product.is_deleted = True

        

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
    existing_shop = db.query(Shop).filter(Shop.shopify_domain == shop.shopify_domain).first()
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
        customer=db.query(ShopCustomer).filter(ShopCustomer.shopify_id == order.customer_id).first()
        if not customer:
            new_customer=ShopCustomer(
                shopify_id=order.customer_id,
                email=order.customer_email,
                mobile=order.customer_phone,
                first_name=order.customer_name,
                billing_mobile_no=order.billing_phone,
                shipping_mobile_no=order.shipping_phone
            )
            db.add(new_customer)
            db.commit()
            db.refresh(new_customer)
        for line_item in order.line_items:
            # Check product in database
            order_date = parser.parse(order.order_date)
            if order_date.tzinfo is None:
                timezone = pytz.timezone("UTC")  # Replace with the relevant timezone if needed
                order_date = timezone.localize(order_date)
            product = db.query(Products).filter(Products.shopify_product_id == line_item.product_id).first()
            if product:
                
            
            # Add the order
                new_order = Orders(
                    shop_id=shop.shop_id,
                    shopify_order_id=order.shopify_order_id,
                    customer_id=customer.shop_customer_id,
                    order_date=order_date,  # Ensure datetime conversion
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
                # print(type(product.reorder_days))  # Should be int or str (string representing int)
                # print(type(order_date))
                reminder_date = order_date + timedelta(days=int(product.reorder_days))
                # print(type(reminder_date))
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

@router.post("/save-settings")
async def save_settings(emailTemplateSettings: EmailTemplateSettings, db: Session = Depends(get_db)):
    
    if emailTemplateSettings:
        print(emailTemplateSettings)
        shop = db.query(Shop).filter(Shop.shopify_domain == emailTemplateSettings.shop_name).first()
        placeholders = {
                            "first_name": "John",
                            "product_name": "Widget Pro",
                            "product_image": "https://via.placeholder.com/150x150.png?text=Widget+Pro",
                            "quantity": "2",
                            "remaining_days": "5",
                            "reorder_url": "https://yourshop.com/reorder/widget-pro",
                        }
        html_content = HTML_TEMPLATE.format(**placeholders)
        if not shop:
            raise HTTPException(status_code=404, detail="Shop not found")
        if emailTemplateSettings.bufferTime:
            shop.buffer_time=emailTemplateSettings.bufferTime
        if emailTemplateSettings.coupon:
            shop.coupon=emailTemplateSettings.coupon

        if emailTemplateSettings.discountPercent:
            shop.discountpercent=emailTemplateSettings.discountPercent
        db.commit()
        db.refresh(shop)
        
        new_message_template = Message_Template(
        message_template=' ',
        message_channel = "email",
        shop_name=emailTemplateSettings.shop_name,
        mail_server = emailTemplateSettings.mail_server,
        port=int(emailTemplateSettings.port),
        fromname = emailTemplateSettings.fromName,
        subject = emailTemplateSettings.subject,
        created_at=datetime.utcnow(),
        modified_at=datetime.utcnow(),
         )
        db.add(new_message_template)
        db.commit()
        db.refresh(new_message_template)

        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] =API_KEY 
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
    
        email_data = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": shop.email}],
            sender={"email": emailTemplateSettings.fromName},
            subject=f"Test Mail: {emailTemplateSettings.subject}",
            html_content=html_content
        )
        try:
            api_instance.send_transac_email(email_data)
            
        except ApiException as e:
            print(f"Error sending email: {e}")
    return {"Your email template has been saved successfully! All future reminders will use this updated template to engage your customers." }


@router.get("/get-settings")
async def get_settings(shop_name: str , db: Session = Depends(get_db),s3: BaseClient = Depends(get_s3_client)):
    # Fetch the shop based on shop_name
    shop = db.query(Shop).filter(Shop.shopify_domain == shop_name).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    s3_path = f"{shop.shop_id}/{shop.shop_logo}"
    client_action='get_object'
    # url = s3.generate_presigned_url(
    #      client_action, Params={"Bucket": AWS_BUCKET, "Key": s3_path}, ExpiresIn = 3600
    # )
    url = f"https://s3.{AWS_REGION_NAME}.amazonaws.com/{AWS_BUCKET}/{s3_path}"
    

    # General settings
    general_settings = {
        "bannerImage":url,
        "bannerImageName":shop.shop_logo
    }

    # Email template settings
    email_template = db.query(Message_Template).filter(Message_Template.shop_name == shop_name).first()
    if email_template:
        email_template_settings = {
            "coupon": shop.coupon,
            "bufferTime": shop.buffer_time,
            "discountPercent": shop.discountpercent,
            "mail_server": email_template.mail_server,
            "port": email_template.port,
            "fromName": email_template.fromname,
            "subject": email_template.subject,
            "message_channel": email_template.message_channel,
        }
    else:
        email_template_settings = None

    settings_data={ "email_template_settings":email_template_settings,"general_settings":general_settings}
    # print(settings_data)
    return settings_data

@router.post("/upload_to_aws/{shop_name}")
async def upload_file_to_server(shop_name:str,db:db_dependency,s3: BaseClient = Depends(get_s3_client),bannerImage: UploadFile = File(...)):
    try:
        shop = db.query(Shop).filter(Shop.shopify_domain ==shop_name).first()
        if not bannerImage:
            raise HTTPException(status_code=400, detail="No file provided")
        folder_name = f"{shop.shop_id}/{bannerImage.filename}"
        s3.upload_fileobj(bannerImage.file, AWS_BUCKET, folder_name)
        
        shop.shop_logo=bannerImage.filename
        db.commit()
        db.refresh(shop)
        return {bannerImage.filename}
    except HTTPException as e:
        raise HTTPException(status_code=400, detail='File Type not Supported')   
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail='Something went wrong')
