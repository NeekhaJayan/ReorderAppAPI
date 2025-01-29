import boto3
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
import os

 
AWS_BUCKET='reorderpro.decagrowth.com'
AWS_ACCESS_KEY_ID=os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY=os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION_NAME='ap-south-1'

s3_resource = boto3.resource('s3',region_name=AWS_REGION_NAME, aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
BUCKET=s3_resource.Bucket(AWS_BUCKET)


AWS_BUCKET='reorderpro.decagrowth.com'
AWS_REGION_NAME='ap-south-1'
API_KEY=os.getenv("SENDINBLUE_API_KEY")

def send_email(to, subject, body, sender_email,sender_name):
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = API_KEY
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
    email_data = sib_api_v3_sdk.SendSmtpEmail(
        to=[{"email": to}],
        sender={"name": sender_name, "email": sender_email},
        subject=subject,
        html_content=body
    )
    try:
        api_instance.send_transac_email(email_data)
        print(f"Email sent to {to}")
        
    except ApiException as e:
        print(f"Error sending email: {e}")


def get_s3_client():
    return boto3.client('s3',region_name=AWS_REGION_NAME, aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)