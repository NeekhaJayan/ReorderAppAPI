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
API_KEY=os.getenv("SENDINBLUE_API_KEY")
def send_email(to, subject, body, sender_email):
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] =API_KEY 
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
        print(body)
        print(subject)
        print(sender_email)
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
                    .filter(Shop.shop_id == reminder.shop_id, Shop.is_deleted == False)
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

                if not customer or not shop or not message_template:
                    print(
                        f"Skipping reminder {reminder.reminder_id}: Missing required data."
                    )
                    continue

                send_email(
                    to=customer.email,
                    subject=message_template.subject,
                    body=message_template.message_template,
                    sender_email=message_template.fromname,
                )

            except Exception as e:
                print(f"Error processing reminder {reminder.reminder_id}: {e}")

    finally:
        # Ensure the database session is closed
        db.close()


# Automatically execute reminders when run directly
if __name__ == "__main__":
    send_reminders()
