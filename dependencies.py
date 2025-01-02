import boto3

import os

 
AWS_BUCKET='reorderpro.decagrowth.com'
AWS_ACCESS_KEY_ID=os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY=os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION_NAME='ap-south-1'

s3_resource = boto3.resource('s3',region_name=AWS_REGION_NAME, aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
BUCKET=s3_resource.Bucket(AWS_BUCKET)



def get_s3_client():
    return boto3.client('s3',region_name=AWS_REGION_NAME, aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)