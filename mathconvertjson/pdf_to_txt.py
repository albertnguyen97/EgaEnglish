from pdfminer.high_level import extract_text
import fitz  # PyMuPDF
import base64


def extract_text_from_pdf(pdf_path, output_txt_path):
    """Đọc văn bản từ file PDF và lưu vào file .txt."""
    pdf_text = extract_text(pdf_path)
    with open(output_txt_path, 'w', encoding='utf-8') as file:
        file.write(pdf_text)
    print(f"Nội dung đã được lưu vào {output_txt_path}")


def extract_images_from_pdf(pdf_path):
    """Trích xuất hình ảnh từ file PDF và chuyển đổi chúng thành base64."""
    pdf_document = fitz.open(pdf_path)
    images_base64 = []

    for page_number in range(len(pdf_document)):
        page = pdf_document.load_page(page_number)
        image_list = page.get_images(full=True)

        for img in image_list:
            xref = img[0]
            base_image = pdf_document.extract_image(xref)
            image_bytes = base_image["image"]
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            images_base64.append(image_base64)

    return images_base64


def update_text_with_images(txt_path, images_base64):
    """Cập nhật nội dung file .txt với hình ảnh dưới dạng base64, xử lý cả các đáp án là ảnh."""
    with open(txt_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    new_content = []
    image_index = 0

    for line in lines:
        new_content.append(line)
        if "ảnh" in line.lower() and image_index < len(images_base64):
            new_content.append(f"\nImage {image_index + 1}:\n{images_base64[image_index]}\n")
            image_index += 1

    # Xóa các dòng có chuỗi "Đúng  Sai"
    filtered_content = [line for line in new_content if "Đúng  Sai" not in line]

    # Xóa các dòng trắng
    non_empty_lines = [line for line in filtered_content if line.strip()]

    # Tìm và thay thế các đáp án là ảnh
    final_content = []
    i = 0
    while i < len(non_empty_lines):
        line = non_empty_lines[i]
        if "Ảnh" in line:
            # Tìm dòng tiếp theo có chứa base64 (đáp án là ảnh)
            if i + 1 < len(non_empty_lines) and "Image" in non_empty_lines[i + 1]:
                final_content.append(f"{line.strip()}\n{non_empty_lines[i + 1].strip()}\n")
                i += 1  # Bỏ qua dòng tiếp theo đã thêm vào
            else:
                final_content.append(line)
        else:
            final_content.append(line)
        i += 1

    with open(txt_path, 'w', encoding='utf-8') as file:
        file.writelines(final_content)

    print(f"Nội dung và hình ảnh đã được cập nhật vào {txt_path}, và các dòng trắng đã được xóa.")



def process_pdf(pdf_path, txt_path):
    """Chạy toàn bộ quy trình: trích xuất văn bản và hình ảnh, cập nhật file .txt."""
    extract_text_from_pdf(pdf_path, txt_path)
    images_base64 = extract_images_from_pdf(pdf_path)
    update_text_with_images(txt_path, images_base64)


# Đường dẫn đến file PDF và file đầu ra
pdf_path = 'markdown4.pdf'
txt_path = 'output1.txt'

# Chạy quy trình
process_pdf(pdf_path, txt_path)
