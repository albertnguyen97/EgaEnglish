from pdfminer.high_level import extract_text
import fitz  # PyMuPDF
import base64
import re
import json

def extract_text_from_pdf(pdf_path):
    """Đọc văn bản từ file PDF."""
    return extract_text(pdf_path)

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

def update_text_with_images(content, images_base64):
    """Cập nhật nội dung văn bản với hình ảnh dưới dạng base64, xử lý cả các đáp án là ảnh."""
    lines = content.splitlines()

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
        if "*Ảnh*" in line:
            # Tìm dòng tiếp theo có chứa base64 (đáp án là ảnh)
            if i + 1 < len(non_empty_lines) and "Image" in non_empty_lines[i + 1]:
                final_content.append(f"{line.strip()}\n{non_empty_lines[i + 1].strip()}\n")
                i += 1  # Bỏ qua dòng tiếp theo đã thêm vào
            else:
                final_content.append(line)
        else:
            final_content.append(line)
        i += 1

    return '\n'.join(final_content)

def parse_questions(content):
    """Phân tích nội dung văn bản và chuyển đổi thành danh sách câu hỏi."""
    questions = []
    # Tách các khối câu hỏi dựa trên tiêu đề phần
    parts = re.split(r'\n(?=PHẦN\s+[IVXLC]+\.)', content.strip())
    print(f"Phần văn bản được phân tách: {len(parts)} phần")

    for part in parts:
        part_title = re.match(r'^PHẦN\s+[IVXLC]+\.\s*(.*)', part, re.IGNORECASE)
        if part_title:
            part_number = part_title.group(0).strip()  # Lấy tiêu đề phần
            part_content = part[len(part_title.group(0)):].strip()
            # Tách các khối câu hỏi trong phần
            question_blocks = re.split(r'\n(?=\s*Câu\s*\d+)', part_content)

            for block in question_blocks:
                lines = block.split('\n')
                question_match = re.match(r'^\s*Câu\s*(\d+):\s*(.+)', lines[0])
                if question_match:
                    question_number = question_match.group(1).strip()
                    full_question_text = question_match.group(2).strip()
                    question_text_lines = [full_question_text]

                    # Xác định loại câu hỏi dựa trên tiêu đề phần
                    if "PHẦN I." in part_number:
                        question_type = "Nhiều Lựa chọn"
                    elif "PHẦN II." in part_number:
                        question_type = "Đúng/Sai"
                    elif "PHẦN III." in part_number:
                        question_type = "Trả lời ngắn"
                    else:
                        question_type = "Không xác định"

                    for line in lines[1:]:
                        if re.match(r'^\s*[A-Da-d][\.\)]\s*', line):
                            break
                        question_text_lines.append(line.strip())

                    # Xử lý ảnh (nếu có)
                    question_text = ' '.join(question_text_lines).strip().split('Ảnh')[0].strip()
                    img_text = None
                    if 'Ảnh' in ' '.join(question_text_lines).strip():
                        img_text = ' '.join(question_text_lines).strip().split('Ảnh', 1)[1].strip()
                        print(f"*Ảnh*: {img_text}")


                    # Xử lý tùy chọn đáp án
                    options = {}
                    current_option = None
                    current_option_text = ""

                    for line in lines[1:]:
                        option_match = re.match(r'^\s*([A-Da-d])[\.\)]\s*(.*)', line)
                        if option_match:
                            if current_option:
                                options[current_option] = current_option_text.strip()
                            current_option = option_match.group(1).strip()
                            current_option_text = option_match.group(2).strip()
                        elif current_option:
                            current_option_text += ' ' + line.strip()

                    if current_option:
                        options[current_option] = current_option_text.strip()

                    options = {k: re.split(r'\s*PHẦN', v)[0].strip() for k, v in options.items()}

                    questions.append({
                        "question_number": question_number,
                        "question": question_text,
                        "type": question_type,
                        "options": options,
                        "img": img_text
                    })

                elif re.match(r'^\s*Câu\s*(\d+)\.\s*(.*)', lines[0]):
                    question_match = re.match(r'^\s*Câu\s*(\d+)\.\s*(.*)', lines[0])
                    if question_match:
                        question_number = question_match.group(1).strip()
                        full_question_text = question_match.group(2).strip()
                        for line in lines[1:]:
                            full_question_text += line.strip() + ' '
                        question_text = full_question_text.split('*Ảnh*')[0].strip()
                        img_text = None
                        if '*Ảnh*' in full_question_text:
                            img_text = full_question_text.split('*Ảnh*', 1)[1].strip()
                            img_text = img_text.split(' ')[2].strip()

                        questions.append({
                            "question_number": question_number,
                            "question": question_text,
                            "type": "Trả lời ngắn",
                            "img": img_text,
                        })

    return questions

def save_to_json(data, output_file):
    """Lưu dữ liệu vào file JSON."""
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def process_pdf_to_json(pdf_path, output_json_path):
    """Quy trình xử lý toàn bộ: trích xuất văn bản và hình ảnh từ PDF, phân tích câu hỏi và lưu vào file JSON."""
    content = extract_text_from_pdf(pdf_path)
    images_base64 = extract_images_from_pdf(pdf_path)
    updated_content = update_text_with_images(content, images_base64)
    questions = parse_questions(updated_content)
    save_to_json(questions, output_json_path)
    print(f"Đã lưu {len(questions)} câu hỏi hợp lệ vào {output_json_path}")

# Đường dẫn đến file PDF và file JSON đầu ra
pdf_path = 'markdown2codapan.pdf'
output_json_path = 'questions1.json'

# Chạy quy trình
process_pdf_to_json(pdf_path, output_json_path)

