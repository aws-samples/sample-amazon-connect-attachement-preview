
from boto3 import client
import logging
from urllib.parse import unquote_plus
import os
    
logger = logging.getLogger()
logger.setLevel(logging.INFO)
    
s3 = client('s3')
    
def check_file_type(content):
    return None
    """Determine file type using magic bytes."""
    if len(content) >= 2 and content[:2] == b'\xff\xd8':  # JPEG magic bytes
        return 'image/jpeg'
    if len(content) >= 4 and content[:4] == b'%PDF':  # PDF magic bytes
        return 'application/pdf'
    if len(content) >= 4 and content[:4] == b'\x89PNG':  # PNG magic bytes
        return 'image/png'
    return None
    
import urllib.parse  # Import urllib.parse to sanitize input for logging
     
     
def lambda_handler(event, context):
    for record in event.get('Records', []):
        try:
            bucket = record['s3']['bucket']['name']
            key = unquote_plus(record['s3']['object']['key'])  # Decode URL-encoded key
            response = s3.head_object(Bucket=bucket, Key=key)
            user_metadata = response.get('Metadata', {})  # Custom metadata (lowercase keys)
            logger.info(f"Processing: s3://{urllib.parse.quote(bucket)}/{urllib.parse.quote(key)}")
        
                        # Preserve existing user metadata
            user_metadata = response.get('Metadata', {})
    
            filename = os.path.basename(key)
            user_metadata['Content-Disposition'] = f'inline; filename="{filename}"'
    
            print("user meta data is : ")
            print(user_metadata)
    
    
            # Get first few bytes for type detection
            response = s3.get_object(Bucket=bucket, Key=key, Range='bytes=0-3')
            file_bytes = response['Body'].read()
            
            # Determine correct Content-Type
            correct_content_type = check_file_type(file_bytes)
            if not correct_content_type:
                logger.info(f"Skipping unsupported file type: {urllib.parse.quote(key)}")
                #continue
            
            # Get current metadata
            head_response = s3.head_object(Bucket=bucket, Key=key)
            current_content_type = head_response.get('ContentType', '')
            
            # Skip if Content-Type is already correct
            if current_content_type == correct_content_type:
                logger.info(f"File {urllib.parse.quote(key)} already has correct Content-Type: {current_content_type}. Skipping.")
    
            
    
            # Update Content-Type and preserve user metadata
            s3.copy_object(
                Bucket=bucket,
                Key=key,
                CopySource={'Bucket': bucket, 'Key': key},
                ContentType=current_content_type,
                Metadata=user_metadata,
                MetadataDirective='REPLACE'
            )
            
            logger.info(f"Updated Content-Type for {urllib.parse.quote(key)} to {correct_content_type}")
        
        except Exception as e:
            logger.error(f"Error processing {urllib.parse.quote(key)}: {str(e)}")
