from pdf2image import convert_from_path
import os

def pdf_to_images(pdf_path, output_folder):
    # Tạo thư mục output nếu chưa tồn tại
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    try:
        # Chuyển đổi PDF thành list các ảnh
        images = convert_from_path(pdf_path)
        
        # Lưu từng trang thành file ảnh
        for i, image in enumerate(images):
            image_path = os.path.join(output_folder, f'page_{i+1}.jpg')
            image.save(image_path, 'JPEG')
            print(f'Đã lưu trang {i+1} tại: {image_path}')
            
        print(f'Đã chuyển đổi thành công {len(images)} trang')
        
    except Exception as e:
        print(f'Có lỗi xảy ra: {str(e)}')

# Sử dụng hàm
pdf_path = '/home/sotatek/Documents/Uyen/panasonic/cffv5mk2-katsuyouguide-20240126zad-ja_secured.pdf'  # Thay đổi đường dẫn đến file PDF của bạn
output_folder = '/home/sotatek/Documents/Uyen/panasonic_reasoning/data/image' # Thay đổi đường dẫn đến thư mục output

pdf_to_images(pdf_path, output_folder)