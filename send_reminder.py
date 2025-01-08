from fastapi import FastAPI
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Products, Shop, Orders, ShopCustomer, OrderProduct, Reminder, Message_Template
from datetime import datetime
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from sqlalchemy import func
import os
app = FastAPI()
AWS_BUCKET='reorderpro.decagrowth.com'
AWS_REGION_NAME='ap-south-1'
API_KEY=os.getenv("SENDINBLUE_API_KEY")

def send_email(to, subject, body, sender_email):
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = API_KEY
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
    email_data = sib_api_v3_sdk.SendSmtpEmail(
        to=[{"email": to}],
        sender={"email": sender_email},
        subject=subject,
        html_content=body
    )
    try:
        api_instance.send_transac_email(email_data)
        print(f"Email sent to {to}")
        
    except ApiException as e:
        print(f"Error sending email: {e}")


def send_reminders():
    # Create a database session
    db = SessionLocal()
    try:
        today = datetime.now().date()
        print(today)
        reminders = (
            db.query(Reminder)
            .filter(func.date(Reminder.reminder_date) == today, Reminder.is_deleted == False)
            .all()
        )
        print(reminders)
        if not reminders:
            print("No reminders to process today.")
            return

        for reminder in reminders:
            try:
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
                print(customer,shop,message_template)
                order=db.query(Orders).filter(Orders.order_id==reminder.order_id).first()
                if not customer or not shop or not message_template:
                    print(
                        f"Skipping reminder {reminder.reminder_id}: Missing required data."
                    )
                    continue
                placeholders={"first_name": customer.first_name,
                              "product_name": reminder.product_title,
                              "quantity": reminder.product_quantity,
                              "remaining_days": shop.buffer_time,
                              "reorder_url":f"https://{shop.shopify_domain}/checkouts/cn/Z2NwLWFzaWEtc291dGhlYXN0MTowMUpIMlRaVkJTNjExS1BTVlcwUkNRWkVCOA?discount=RESTOCK10",
                              "image_path":f"https://s3.{AWS_REGION_NAME}.amazonaws.com/{AWS_BUCKET}/{shop.shop_id}/{shop.shop_logo}"
                              }
                print(placeholders)
                # f"https://{shop.shopify_domain}/cart/{order.shopify_order_id}/d64bec3cd4c972b4e7dc28ee22c3f888/authenticate?key=ee33950610339185a714e5d9c130d267",
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
                        color: #202223;
                        height: 100%;
                        overflow: auto;
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
                        <img src={placeholders["image_path"]} alt="Shop Logo" />
                        
                      </div>
                      <div class="content">
                        <p>Hello {placeholders["first_name"]},</p>
                        <p>Your <strong>{placeholders["product_name"]}</strong> might be running low. Don't worry – you can reorder with just one click!</p>
                        <div class="product-section">
                          <img src="https://via.placeholder.com/150x150.png?text=Product+Image" alt="{placeholders["product_name"]}" />
                          <p><strong>Product Name:</strong> {placeholders["product_name"]}</p>
                          <p><strong>Quantity Ordered:</strong> {placeholders["quantity"]}</p>
                          <p><strong>Estimated Days Remaining:</strong> {placeholders["remaining_days"]}</p>
                        </div>
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
                send_email(
                    to=customer.email,
                    subject=message_template.subject,
                    body=email_template,
                    sender_email=message_template.fromname,
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
