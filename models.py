from sqlalchemy import Boolean, Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class Shop(Base):
    __tablename__ = "shop"

    shop_id = Column(Integer, primary_key=True, index=True)
    shopify_domain = Column(String, index=True)  # Shopify domain is a string
    shop_name = Column(String, index=True)  # Shop name is a string
    shop_logo = Column(String, nullable=True)  # Logo path or URL as string
    email = Column(String, index=True)  # Email should be a string
    message_template_id = Column(Integer, nullable=True)  # Assuming template ID is an integer
    created_at = Column(DateTime, default=datetime.utcnow)
    modified_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)  # Boolean to indicate deletion


class ShopCustomer(Base):
    __tablename__ = "shop_customer"

    shop_customer_id = Column(Integer, primary_key=True, index=True)
    shopify_id = Column(String, index=True)  # Shopify ID is a string
    email = Column(String, index=True)  # Email should be a string
    mobile = Column(String, index=True)  # Mobile number as a string
    first_name = Column(String, index=True)  # First name is a string
    created_at = Column(DateTime, default=datetime.utcnow)
    modified_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)  # Boolean for deletion


class OrderProduct(Base):
    __tablename__ = "order_product"

    order_product_id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), index=True)  # Relates to orders
    email = Column(String, index=True)  # Email should be a string
    shopify_product_id = Column(Integer, index=True)  # Assuming it's an integer
    quantity = Column(Integer, index=True)  # Quantity as integer
    created_at = Column(DateTime, default=datetime.utcnow)
    modified_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)


class Orders(Base):
    __tablename__ = "orders"

    order_id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shop.shop_id"), index=True)  # Relates to shop
    shopify_order_id = Column(String, index=True)  # Shopify order ID is a string
    customer_id = Column(Integer, ForeignKey("shop_customer.shop_customer_id"), index=True)  # Relates to customer
    order_date = Column(DateTime, index=True)  # Date should be a DateTime
    total_amount = Column(Float, index=True)  # Total amount as float
    status = Column(String, index=True)  # Order status as a string
    created_at = Column(DateTime, default=datetime.utcnow)
    modified_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(Boolean, default=False)


class Products(Base):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shop.shop_id"), index=True)  # Relates to shop
    shopify_product_id = Column(String, index=True)  # Shopify product ID is a string
    title = Column(String, index=True)  # Product title as a string
    reorder_days = Column(Integer, index=True)  # Reorder days as integer
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)


class Reminder(Base):
    __tablename__ = "reminder"

    reminder_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("shop_customer.shop_customer_id"), index=True)  # Relates to customer
    product_id = Column(Integer, ForeignKey("products.product_id"), index=True)  # Relates to product
    order_id = Column(Integer, ForeignKey("orders.order_id"), index=True)  # Relates to order
    reminder_date = Column(DateTime, index=True)  # Date should be DateTime
    status = Column(String, index=True)  # Reminder status as string
    created_at = Column(DateTime, default=datetime.utcnow)
    modified_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
