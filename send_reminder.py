from fastapi import FastAPI
from sqlalchemy.orm import Session
from database import SessionLocal
from dependencies import send_email
from models import Products, Shop, Orders, ShopCustomer, OrderProduct, Reminder, Message_Template
from datetime import datetime
from sqlalchemy import func
import os
from jinja2 import Template

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
                    url=f"https://rrpapp.decagrowth.com/redirect?shop_domain={shop.shopify_domain}&variant_id={reminder_product.shopify_variant_id}&quantity={reminder.product_quantity}"
                  else:
                    url=f"https://rrpapp.decagrowth.com/redirect?shop_domain={shop.shopify_domain}&variant_id={reminder_product.shopify_variant_id}&quantity={reminder.product_quantity}&coupon={shop.coupon}"
                  print(url)
                  placeholders={"first_name": customer.first_name,
                                "product_name": reminder.product_title,
                                "shop":shop.shop_name,
                                "product_image":reminder.image_url,
                                "quantity": reminder.product_quantity,
                                "mail_to":shop.email,
                                "remaining_days": shop.buffer_time,
                                "reorder_url":url,
                                "image_path":f"https://s3.{AWS_REGION}.amazonaws.com/{AWS_BUCKET}/{shop.shop_id}/{shop.shop_logo}",
                                "shop": shop.shop_name,
                                "plan": shop.plan,
                                "coupon": shop.coupon or "",
                                "discountpercent": shop.discountpercent or "0"

                                }
                  # https://deca-development-store.myshopify.com/cart/clear?return_to=/cart/add?items[][id]=42034558533741&items[][quantity]=1&return_to=/checkout?discount=EXTRA5
                  print(customer.first_name,message_template.fromname)
                  print(url)
                  print(placeholders["image_path"])
                  
                  # coupon_section = f"""
                  #                   <tr>
                  #                     <td align="center" bgcolor="#f9f1dc" style="padding:15px; border-radius:5px;">
                  #                       <h3 style="color:#d67e00; margin:0;">SPECIAL OFFER</h3>
                  #                       <p style="font-size:16px;">Use code <span style="font-size:18px; font-weight:bold; color:#d67e00; background:#fff; padding:5px 10px; border-radius:4px;">{shop.coupon}</span> at checkout</p>
                  #                       <p style="font-size:16px;">Save {shop.discountpercent}% on your reorder</p>
                  #                     </td>
                  #                   </tr>
                  #                   """ if shop.coupon else f""
                  # logo_image_section =f"""
                  #                       <tr>
                  #                               <td align="center" bgcolor="#eeeeee" style="padding:20px; border-radius:8px 8px 0 0;">
                  #                                 <img src="{placeholders["image_path"]}" alt="{placeholders["shop"]}" width="120" style="display:block;">
                  #                                 <h1 style="font-size:24px; color:#333333; font-family:Arial, sans-serif;">Time to Restock!</h1>
                  #                               </td>
                  #                             </tr> """ if shop.shop_logo else f"""
                  #                             <tr>
                  #                               <td align="center" bgcolor="#eeeeee" style="padding:20px; border-radius:8px 8px 0 0;">
                  #                                 <h1 style="font-size:30px; color:#333333; font-family:Arial, sans-serif;">{placeholders["shop"]}</h1>
                  #                                 <h1 style="font-size:24px; color:#333333; font-family:Arial, sans-serif;">Time to Restock!</h1>
                  #                               </td>
                  #                             </tr> """
                  
                  # email_template=f'''<!DOCTYPE html>
                                    # <html>
                                    # <head>
                                    #   <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
                                    #   <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                                    # </head>
                                    # <body style="margin:0; padding:0; background-color:#f4f4f4;">
                                    #   <table role="presentation" width="100%" bgcolor="#f4f4f4" cellpadding="0" cellspacing="0" border="0">
                                    #     <tr>
                                    #       <td align="center">
                                    #         <table role="presentation" width="600" bgcolor="#ffffff" cellpadding="0" cellspacing="0" border="0" style="margin:20px auto; padding:20px; border-radius:8px;">
                                              
                                    #           {logo_image_section}
                                              
                                    #           <tr>
                                    #             <td align="center" style="padding:20px; font-family:Arial, sans-serif; color:#333333;">
                                    #               <p style="font-size:16px;">Hello {placeholders["first_name"]},</p>
                                    #               <p style="font-size:16px;">We noticed it's been <b>{placeholders["remaining_days"]}</b> days since you purchased <b>{placeholders["product_name"]}</b>. You might be running low!</p>
                                    #               <p style="font-size:16px;">Don't wait until you run out! Restock now and keep enjoying your favorite products.</p>
                                    #             </td>
                                    #           </tr>

                                    #           <tr>
                                    #             <td align="center" style="padding:10px;">
                                    #               <img src="{placeholders["product_image"]}" alt="{placeholders["product_name"]}" width="150" style="display:block; margin:0 auto; border-radius:5px;">
                                    #             </td>
                                    #           </tr>
                                    #           <tr>
                                    #             <td align="center" style="padding:5px 20px; font-family:Arial, sans-serif;">
                                    #               <h3 style="font-size:18px; color:#333333;">{placeholders["product_name"]}</h3>
                                    #               <p style="font-size:14px;"><b>Quantity:</b> {placeholders["quantity"]}</p>
                                    #             </td>
                                    #           </tr>

                                    #           <tr>
                                    #             <td align="center" style="padding:20px;">
                                    #               <a href="{placeholders["reorder_url"]}" target="_blank" style="display:inline-block; padding:12px 20px; background-color:#007bff; color:#ffffff; text-decoration:none; border-radius:5px; font-size:16px; font-weight:bold;">
                                    #                 REORDER NOW
                                    #               </a>
                                    #             </td>
                                    #           </tr>

                                    #           {coupon_section}

                                    #           <tr>
                                    #             <td align="center" style="padding:20px; font-size:12px; color:#777777; font-family:Arial, sans-serif;">
                                    #               <p>{placeholders["shop"]} | {placeholders["mail_to"]} </p>
                                    #               <p>Powered by <b>ReOrder Reminder Pro</b></p>
                                    #             </td>
                                    #           </tr>

                                    #         </table>
                                    #       </td>
                                    #     </tr>
                                    #   </table>
                                    # </body>
                                    # </html>

                                    # '''
                  
                  template_str = message_template.body_template
                  template = Template(template_str)
                  email_template = template.render(**placeholders)
                  
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
