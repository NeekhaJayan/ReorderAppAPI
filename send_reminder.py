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
AWS_REGION=os.getenv("AWS_REGION_NAME")
# AWS_REGION = "ap-south-1"



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

                  if shop.plan=='Free':
                    url=f"https://reorder-shopify-app.onrender.com/redirect?shop_domain={shop.shopify_domain}&variant_id={reminder_product.shopify_variant_id}&quantity={reminder.product_quantity}"
                  else:
                    url=f"https://reorder-shopify-app.onrender.com/redirect?shop_domain={shop.shopify_domain}&variant_id={reminder_product.shopify_variant_id}&quantity={reminder.product_quantity}&coupon={shop.coupon}"
                  print(url)
                  placeholders={"first_name": customer.first_name,
                                "product_name": reminder.product_title,
                                "shop":shop.shop_name,
                                "product_image":reminder.image_url,
                                "quantity": reminder.product_quantity,
                                "mail_to":shop.email,
                                "remaining_days": shop.buffer_time,
                                "reorder_url":url,
                                "image_path":f"https://s3.{AWS_REGION}.amazonaws.com/{AWS_BUCKET}/{shop.shop_id}/{shop.shop_logo}"
                                }
                  # https://deca-development-store.myshopify.com/cart/clear?return_to=/cart/add?items[][id]=42034558533741&items[][quantity]=1&return_to=/checkout?discount=EXTRA5
                  print(customer.first_name,message_template.fromname)
                  print(url)
                  print(placeholders["image_path"])
                  # email_template=f'''<!DOCTYPE html>
                  #   <html>
                  #   <head>
                  #     <title>Reorder Reminder</title>
                  #     <style>
                  #       body {{
                  #         font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                  #         margin: 0;
                  #         padding: 0;
                  #         background-color: #f9fafb;
                  #         color: rgb(3, 3, 3);
                  #         height: 100%;
                  #         overflow: auto;
                  #       }}
                  #       .email-container {{
                  #         margin: 40px auto;
                  #         background: #ffffff;
                  #         border: 1px solid #dbe1e6;
                  #         border-radius: 8px;
                  #         overflow: hidden;
                  #         box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                  #         min-height: 1200px; 
                  #       }}
                  #       .header {{
                  #         background-color: #efeee7;
                  #         text-align: center;
                  #         padding: 20px;
                  #         color: black;
                  #       }}
                  #       .header img {{
                  #         max-width: 100px; 
                  #         height: auto;     
                  #       }}
                  #       .content {{
                  #         padding: 20px;
                  #       }}
                  #       .product-section {{
                  #         text-align: center;
                  #         margin: 20px 0;
                  #       }}
                  #       .cta {{
                  #         text-align: center;
                  #         margin: 20px 0;
                  #       }}
                  #       .cta a {{
                  #         text-decoration: none;
                  #         color: white;
                  #         background-color: black;
                  #         padding: 10px 20px;
                  #         border-radius: 4px;
                  #       }}
                  #       .coupon {{
                  #         text-align: center;
                  #         margin: 10px 0;
                  #         font-size: 14px;
                  #         background-color:white;
                  #         color:black;
                  #         padding: 10px;
                  #         border-radius: 4px;
                  #         border: 2px dotted #efeee7; /* Dotted border */
                  #         position: relative;
                  #       }}
                  #       .coupon::before {{
                  #         content: "Pro Plan Only";
                  #         position: absolute;
                  #         top: -10px;
                  #         left: 50%;
                  #         transform: translateX(-50%);
                  #         background-color:transparent;
                  #         color: black;
                  #         font-size: 12px;
                  #         padding: 2px 6px;
                  #         border-radius: 4px;
                  #       }}
                  #       .footer {{
                  #         text-align: center;
                  #         padding: 10px;
                  #         font-size: 12px;
                  #         color: #8c9196;
                  #       }}
                  #       @media screen and (max-width: 600px) {{
                  #       .product-section {{
                  #         display: flex;
                  #         flex-direction: column;
                  #         align-items: center;
                  #       }}
  
                  #     .product-section td {{
                  #       display: block;
                  #       width: 100%;
                  #       text-align: center;
                  #     }}

                  #       .product-section td img {{
                  #         max-width: 100%;
                  #         height: auto;
                  #         margin-bottom: 10px;
                  #       }}
                  #     }}

                  #     </style>
                  #   </head>
                  #   <body>
                  #     <div class="email-container">
                  #       <div class="header">
                  #         <img src="{placeholders["image_path"]}" alt="Shop Logo" />
                  #         <h1>{placeholders["shop"]}</h1>
                  #       </div>
                  #       <div class="content">
                  #         <p>Hello {placeholders["first_name"]},</p>
                  #         <p>Your <strong>{placeholders["product_name"]}</strong> might be running low. Don't worry – you can reorder with just one click!</p>
                  #         <table class="product-section" align="center" width="100%" cellspacing="0" cellpadding="10" border="0">
                  #           <tr>
                  #             <td align="center">
                  #               <img src="{placeholders["product_image"]}" 
                  #                   alt="{placeholders["product_name"]}" 
                  #                   width="200" height="auto"
                  #                   style="display: block; max-width: 200px; height: auto; border-radius: 4px;" />
                  #             </td>
                  #             <td align="left" width="70%">
                  #                     <p><strong>Product Name:</strong> {placeholders["product_name"]}</p>
                  #                     <p><strong>Quantity Ordered:</strong> {placeholders["quantity"]}</p>
                  #                     <p><strong>Estimated Days Remaining:</strong> {placeholders["remaining_days"]}</p>
                  #             </td>
                              
                  #           </tr>
                  #         </table>

                  #         <div class="cta">
                  #           <a href="{placeholders["reorder_url"]}" target="_blank">Reorder Now and Save 10%</a>
                  #         </div>
                  #         <div class="coupon">
                  #           Use code <strong>RESTOCK10</strong> at checkout to save 10% on your reorder.
                  #         </div>
                  #       </div>
                  #       <div class="footer">
                  #         <p>Powered by ReOrder Reminder Pro</p>
                  #         <p>Need help? <a href="mailto:{placeholders["mail_to"]}">{placeholders["mail_to"]}</a></p>
                  #       </div>
                  #     </div>
                  #   </body>
                  #   </html>'''
                  #  print(email_template)
                  coupon_section = f"""
                                    <tr>
                                      <td align="center" bgcolor="#f9f1dc" style="padding:15px; border-radius:5px;">
                                        <h3 style="color:#d67e00; margin:0;">SPECIAL OFFER</h3>
                                        <p style="font-size:16px;">Use code <span style="font-size:18px; font-weight:bold; color:#d67e00; background:#fff; padding:5px 10px; border-radius:4px;">{shop.coupon}</span> at checkout</p>
                                        <p style="font-size:16px;">Save {shop.discountpercent}% on your reorder</p>
                                      </td>
                                    </tr>
                                    """ if shop.coupon else f""
                  logo_image_section =f"""
                                        <tr>
                                                <td align="center" bgcolor="#eeeeee" style="padding:20px; border-radius:8px 8px 0 0;">
                                                  <img src="{placeholders["image_path"]}" alt="{placeholders["shop"]}" width="120" style="display:block;">
                                                  <h1 style="font-size:24px; color:#333333; font-family:Arial, sans-serif;">Time to Restock!</h1>
                                                </td>
                                              </tr> """ if shop.shop_logo else f"""
                                              <tr>
                                                <td align="center" bgcolor="#eeeeee" style="padding:20px; border-radius:8px 8px 0 0;">
                                                  <h1 style="font-size:30px; color:#333333; font-family:Arial, sans-serif;">{placeholders["shop"]}</h1>
                                                  <h1 style="font-size:24px; color:#333333; font-family:Arial, sans-serif;">Time to Restock!</h1>
                                                </td>
                                              </tr> """
                  email_template=f'''<!DOCTYPE html>
                                    <html>
                                    <head>
                                      <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
                                      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                                    </head>
                                    <body style="margin:0; padding:0; background-color:#f4f4f4;">
                                      <table role="presentation" width="100%" bgcolor="#f4f4f4" cellpadding="0" cellspacing="0" border="0">
                                        <tr>
                                          <td align="center">
                                            <table role="presentation" width="600" bgcolor="#ffffff" cellpadding="0" cellspacing="0" border="0" style="margin:20px auto; padding:20px; border-radius:8px;">
                                              
                                              {logo_image_section}
                                              
                                              <tr>
                                                <td align="center" style="padding:20px; font-family:Arial, sans-serif; color:#333333;">
                                                  <p style="font-size:16px;">Hello {placeholders["first_name"]},</p>
                                                  <p style="font-size:16px;">We noticed it's been <b>{placeholders["remaining_days"]}</b> days since you purchased <b>{placeholders["product_name"]}</b>. You might be running low!</p>
                                                  <p style="font-size:16px;">Don't wait until you run out! Restock now and keep enjoying your favorite products.</p>
                                                </td>
                                              </tr>

                                              <tr>
                                                <td align="center" style="padding:10px;">
                                                  <img src="{placeholders["product_image"]}" alt="{placeholders["product_name"]}" width="150" style="display:block; margin:0 auto; border-radius:5px;">
                                                </td>
                                              </tr>
                                              <tr>
                                                <td align="center" style="padding:5px 20px; font-family:Arial, sans-serif;">
                                                  <h3 style="font-size:18px; color:#333333;">{placeholders["product_name"]}</h3>
                                                  <p style="font-size:14px;"><b>Quantity:</b> {placeholders["quantity"]}</p>
                                                </td>
                                              </tr>

                                              <tr>
                                                <td align="center" style="padding:20px;">
                                                  <a href="{placeholders["reorder_url"]}" target="_blank" style="display:inline-block; padding:12px 20px; background-color:#007bff; color:#ffffff; text-decoration:none; border-radius:5px; font-size:16px; font-weight:bold;">
                                                    REORDER NOW
                                                  </a>
                                                </td>
                                              </tr>

                                              {coupon_section}

                                              <tr>
                                                <td align="center" style="padding:20px; font-size:12px; color:#777777; font-family:Arial, sans-serif;">
                                                  <p>{placeholders["shop"]} | {placeholders["mail_to"]} </p>
                                                  <p>Powered by <b>ReOrder Reminder Pro</b></p>
                                                </td>
                                              </tr>

                                            </table>
                                          </td>
                                        </tr>
                                      </table>
                                    </body>
                                    </html>

                                    '''
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
