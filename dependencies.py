import boto3
from botocore.exceptions import ClientError
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

 
AWS_BUCKET='reorderpro.decagrowth.com'
AWS_ACCESS_KEY_ID=os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY=os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION="ap-south-1"

s3_resource = boto3.resource('s3',region_name=AWS_REGION, aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
BUCKET=s3_resource.Bucket(AWS_BUCKET)


# def send_email(to, subject, body, sender_email,sender_name):
#     configuration = sib_api_v3_sdk.Configuration()
#     configuration.api_key['api-key'] = API_KEY
#     api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
#     email_data = sib_api_v3_sdk.SendSmtpEmail(
#         to=[{"email": to}],
#         sender={"name": sender_name, "email": sender_email},
#         subject=subject,
#         html_content=body
#     )
#     try:
#         api_instance.send_transac_email(email_data)
#         print(f"Email sent to {to}")
        
#     except ApiException as e:
#         print(f"Error sending email: {e}")

def send_email(to, subject, body, sender_email,sender_name):
    CONFIGURATION_SET = "my-first-configuration-set"
    SENDER=f'{sender_name}<{sender_email}>'
    CHARSET = "UTF-8"
    client = boto3.client('ses',region_name=AWS_REGION,aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    try:
    #Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    to,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': body,
                    },
                    
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': subject,
                },
            },
            Source=send_email,
            # If you are not using a configuration set, comment or delete the
            # following line
            ConfigurationSetName=CONFIGURATION_SET,
        )
# Display an error if something goes wrong.	
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])


def get_s3_client():
    return boto3.client('s3',region_name=AWS_REGION, aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

