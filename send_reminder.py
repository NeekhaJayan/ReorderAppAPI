from fastapi import FastAPI
from sqlalchemy.orm import Session
from database import SessionLocal
from dependencies import send_email
from models import Products, Shop, Orders, ShopCustomer, OrderProduct, Reminder, Message_Template
from datetime import datetime
from sqlalchemy import func
import os
app = FastAPI()


AWS_BUCKET=os.getenv("AWS_BUCKET")
AWS_REGION_NAME=os.getenv("AWS_REGION_NAME")

def send_reminders():
    # Create a database session
    db = SessionLocal()
    try:
        today = datetime.now().date()
        print(today)
        reminders = (
            db.query(Reminder)
            .filter(func.date(Reminder.reminder_date) == today, Reminder.is_deleted == False ,Reminder.status=="Pending")
            .all()
        )
        print(reminders)
        if not reminders:
            print("No reminders to process today.")
            return

        for reminder in reminders:
            try:
                reminder_product=db.query(Products).filter((Products.product_id==reminder.product_id)&(Products.is_deleted==False)).first()
                if reminder_product:
                  customer = (
                      db.query(ShopCustomer)
                      .filter(
                          ShopCustomer.shop_customer_id == reminder.customer_id,
                          ShopCustomer.is_deleted == False,
                      )
                      .first()
                  )

                  shop = (
                      db.query(Shop)
                      .filter(Shop.shopify_domain == reminder.shop_id, Shop.is_deleted == False)
                      .first()
                  )

                  message_template = (
                      db.query(Message_Template)
                      .filter(
                          Message_Template.shop_name == shop.shopify_domain,
                          Message_Template.is_deleted == False,
                      )
                      .first()
                  )
                  
                  order=db.query(Orders).filter(Orders.order_id==reminder.order_id).first()
                  if not customer or not shop or not message_template:
                      print(
                          f"Skipping reminder {reminder.reminder_id}: Missing required data."
                      )
                      continue
                  placeholders={"first_name": customer.first_name,
                                "product_name": reminder.product_title,
                                "shop":shop.shop_name,
                                "product_image":reminder.image_url,
                                "quantity": reminder.product_quantity,
                                "remaining_days": shop.buffer_time,
                                "reorder_url":f"https://{shop.shopify_domain}/checkouts/cn/Z2NwLWFzaWEtc291dGhlYXN0MTowMUpIMlRaVkJTNjExS1BTVlcwUkNRWkVCOA?discount=RESTOCK10",
                                "image_path":f"https://s3.{AWS_REGION_NAME}.amazonaws.com/{AWS_BUCKET}/{shop.shop_id}/{shop.shop_logo}"
                                }
                  
                  print(customer.first_name,message_template.fromname)
                  email_template=f'''<!DOCTYPE html>
                    <html>
                    <head>
                      <title>Reorder Reminder</title>
                      <style>
                        body {{
                          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                          margin: 0;
                          padding: 0;
                          background-color: #f9fafb;
                          color: rgb(3, 3, 3);
                          height: 100%;
                          overflow: auto;
                        }}
                        .email-container {{
                          margin: 40px auto;
                          background: #ffffff;
                          border: 1px solid #dbe1e6;
                          border-radius: 8px;
                          overflow: hidden;
                          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                          min-height: 1200px; 
                        }}
                        .header {{
                          background-color: #efeee7;
                          text-align: center;
                          padding: 20px;
                          color: black;
                        }}
                        .header img {{
                          max-width: 100px; 
                          height: auto;     
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
                          background-color: black;
                          padding: 10px 20px;
                          border-radius: 4px;
                        }}
                        .coupon {{
                          text-align: center;
                          margin: 10px 0;
                          font-size: 14px;
                          background-color:white;
                          color:black;
                          padding: 10px;
                          border-radius: 4px;
                          border: 2px dotted #efeee7; /* Dotted border */
                          position: relative;
                        }}
                        .coupon::before {{
                          content: "Pro Plan Only";
                          position: absolute;
                          top: -10px;
                          left: 50%;
                          transform: translateX(-50%);
                          background-color:transparent;
                          color: black;
                          font-size: 12px;
                          padding: 2px 6px;
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
                          <img src="{placeholders["image_path"]}" alt="Shop Logo" />
                          <h1>{placeholders["shop"]}</h1>
                        </div>
                        <div class="content">
                          <p>Hello {placeholders["first_name"]},</p>
                          <p>Your <strong>{placeholders["product_name"]}</strong> might be running low. Don't worry – you can reorder with just one click!</p>
                          <table class="product-section" align="center" width="100%" cellspacing="0" cellpadding="10" border="0">
                            <tr>
                              <td align="center">
                                <img src="{placeholders["product_image"]}" 
                                    alt="{placeholders["product_name"]}" 
                                    width="200" height="auto"
                                    style="display: block; max-width: 200px; height: auto; border-radius: 4px;" />
                              </td>
                              <td align="left" width="70%">
                                      <p><strong>Product Name:</strong> {placeholders["product_name"]}</p>
                                      <p><strong>Quantity Ordered:</strong> {placeholders["quantity"]}</p>
                                      <p><strong>Estimated Days Remaining:</strong> {placeholders["remaining_days"]}</p>
                              </td>
                              
                            </tr>
                          </table>

                          <div class="cta">
                            <a href="{placeholders["reorder_url"]}" target="_blank">Reorder Now and Save 10%</a>
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
                    </html>'''
                  # print(email_template)
                  senderName =shop.shop_name
                  send_email(
                      to=customer.email,
                      subject=message_template.subject,
                      body=email_template,
                      sender_email=message_template.fromemail,
                      sender_name=message_template.fromname
                  )

                
                  reminder.status='Send'
                  db.commit()

                    

            except Exception as e:
                print(f"Error processing reminder {reminder.reminder_id}: {e}")

    finally:
        # Ensure the database session is closed
        db.close()


# Automatically execute reminders when run directly
if __name__ == "__main__":
    send_reminders()
