# from google.cloud import storage
# import os
# from dotenv import load_dotenv

# load_dotenv()

# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# def upload_to_gcs(bucket_name: str, source_file_path: str, destination_blob_name: str) -> str:
#     """
#     Upload một file lên Google Cloud Storage
    
#     Args:
#         bucket_name: Tên của bucket trên GCS
#         source_file_path: Đường dẫn đến file cần upload
#         destination_blob_name: Tên file sẽ được lưu trên GCS
        
#     Returns:
#         URL công khai của file đã upload
#     """
#     try:
#         storage_client = storage.Client()
    
#         bucket = storage_client.bucket(bucket_name)
    
#         blob = bucket.blob(destination_blob_name)
        
#         blob.upload_from_filename(source_file_path)
        
#         blob.make_public()
#         public_url = blob.public_url
        
#         return public_url
        
#     except Exception as e:
#         print(f"Có lỗi xảy ra khi upload file: {str(e)}")
#         raise


# # bucket_name = "prod-notex-static-bucket"
# # source_file = "/home/sotatek/Documents/AI-NoteX/data/background_data.json"
# # destination_blob = "audio-files/background_data.json"
# # public_url = upload_to_gcs(bucket_name, source_file, destination_blob)
