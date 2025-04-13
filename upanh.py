import os
import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv
from dataplane import s3_upload
from datetime import datetime
from commons.logger_setup import setup_logger
from commons.server_health_check import send_health_status

# Thiết lập đường dẫn cơ sở
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Thiết lập logging
logger = setup_logger('cloudflare_upload', os.path.join(BASE_DIR, 'logs', 'cloudflare_upload.log'), log_to_console=True)

# Load environment variables
load_dotenv()

# Environment variables
ACCOUNT_ID = os.environ.get("ACCOUNT_ID")
CLIENT_ACCESS_KEY = os.environ.get("CLIENT_ACCESS_KEY")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
BUCKET_AUDIO = os.environ.get("BUCKET_AUDIO_NAME")
PUBLIC_R2_AUDIO = os.environ.get("PUBLIC_R2_AUDIO")

# Kiểm tra các biến môi trường
required_env_vars = ["ACCOUNT_ID", "CLIENT_ACCESS_KEY", "CLIENT_SECRET", "BUCKET_AUDIO_NAME", "PUBLIC_R2_AUDIO"]
missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
if missing_vars:
    logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    raise ValueError("Missing required environment variables")

def upload_to_cloudflare_storage(source_file_path, bucket_target=BUCKET_AUDIO, share=False):
    try:
        logger.info(f"Attempting to upload file: {source_file_path}")
        ConnectionUrl = f"https://{ACCOUNT_ID}.r2.cloudflarestorage.com" 
        s3_client = boto3.client(
            's3',
            endpoint_url=ConnectionUrl,
            aws_access_key_id=CLIENT_ACCESS_KEY,
            aws_secret_access_key=CLIENT_SECRET,
            config=Config(signature_version='s3v4'),
            region_name='us-east-1'
        )
        
        if not os.path.exists(source_file_path):
            logger.error(f"Source file does not exist: {source_file_path}")
            return None
        
        file_name, file_extension = os.path.splitext(os.path.basename(source_file_path))
        if file_extension.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            file_type = "images"
        elif file_extension.lower() in ['.mp3', '.wav', '.aac', '.ogg', '.flac', '.m4a']:
            file_type = "audio"
        else:
            file_type = "document"
            
        if share:
            new_file_name = f"share/{file_type}/{file_name}{file_extension}"
        else:
            new_file_name = f"{file_type}/{file_name}{file_extension}"
        
        bucket = BUCKET_AUDIO if bucket_target == "audio" else bucket_target
        
        logger.info(f"Uploading to bucket: {bucket}")
        upload_result = s3_upload(
            Bucket=bucket,
            S3Client=s3_client,
            TargetFilePath=new_file_name,
            SourceFilePath=source_file_path,
            UploadMethod="File"
        )
        
        url = f"{PUBLIC_R2_AUDIO}/{upload_result['Path']}"
        logger.info(f"File uploaded successfully. URL: {url}")
        return url
    except (BotoCoreError, ClientError) as e:
        error_message = f"AWS error occurred: {str(e)}"
        logger.error(error_message)
        send_health_status(error_message, group="server")
    except Exception as e:
        error_message = f"Unexpected error occurred: {str(e)}"
        logger.error(error_message)
        send_health_status(error_message, group="server")
    return None

def upload_images_from_folder(folder_path, output_file="image_urls.txt"):
    """
    Upload all images from a folder and save their URLs to a file.
    
    Args:
        folder_path (str): Path to the folder containing images
        output_file (str): Path to the file where URLs will be saved
    """
    try:
        if not os.path.exists(folder_path):
            logger.error(f"Folder does not exist: {folder_path}")
            return
            
        # Get all files in the folder
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        image_files = [f for f in os.listdir(folder_path) if 
                      os.path.splitext(f)[1].lower() in image_extensions]
        
        if not image_files:
            logger.info(f"No image files found in {folder_path}")
            return
            
        # Create or open the output file
        with open(output_file, 'w') as f:
            for image_file in image_files:
                image_path = os.path.join(folder_path, image_file)
                url = upload_to_cloudflare_storage(image_path)
                if url:
                    f.write(f"{image_file}: {url}\n")
                    logger.info(f"Saved URL for {image_file}")
                    
        logger.info(f"All image URLs have been saved to {output_file}")
        
    except Exception as e:
        error_message = f"Error processing images: {str(e)}"
        logger.error(error_message)
        send_health_status(error_message, group="server")

def simple_upload_to_cloudflare(source_file_path, bucket_target_path):
    """
    Tải file lên Cloudflare R2 với đường dẫn đích được chỉ định.
    
    Args:
        source_file_path (str): Đường dẫn đến file cần tải lên
        bucket_target_path (str): Đường dẫn đích trong bucket (ví dụ: 'folder/subfolder/file.txt')
    
    Returns:
        str: URL công khai của file đã tải lên hoặc None nếu có lỗi
    """
    try:
        logger.info(f"Attempting to upload file: {source_file_path}")
        ConnectionUrl = f"https://{ACCOUNT_ID}.r2.cloudflarestorage.com" 
        s3_client = boto3.client(
            's3',
            endpoint_url=ConnectionUrl,
            aws_access_key_id=CLIENT_ACCESS_KEY,
            aws_secret_access_key=CLIENT_SECRET,
            config=Config(signature_version='s3v4'),
            region_name='us-east-1'
        )
        
        if not os.path.exists(source_file_path):
            logger.error(f"Source file does not exist: {source_file_path}")
            return None
            
        upload_result = s3_upload(
            Bucket=BUCKET_AUDIO,
            S3Client=s3_client,
            TargetFilePath=bucket_target_path,
            SourceFilePath=source_file_path,
            UploadMethod="File"
        )
        
        url = f"{PUBLIC_R2_AUDIO}/{upload_result['Path']}"
        logger.info(f"File uploaded successfully. URL: {url}")
        return url
        
    except (BotoCoreError, ClientError) as e:
        error_message = f"AWS error occurred: {str(e)}"
        logger.error(error_message)
        send_health_status(error_message, group="server")
    except Exception as e:
        error_message = f"Unexpected error occurred: {str(e)}"
        logger.error(error_message)
        send_health_status(error_message, group="server")
    return None

if __name__ == "__main__":
    image_folder = "/Users/uyenbaby/Downloads/panasonic_reasoning/image"
    upload_images_from_folder(image_folder)